Vue.config.delimiters = ['{$', '$}'];
Vue.config.unsafeDelimiters = ['{$$', '$$}'];
Vue.config.debug = true;

Vue.filter('calendarDate', function (value) {
    return moment(value).calendar();
});

var ProgramDetailsComponent = Vue.extend({
    replace: false,

    data: function() {
        return {
            program: {},
            selectedReportType: 'snapshot',
            fetchInterval: null,
            editNameMode: false,
            gage: {},
            scoreRanges: [
                {low: 0, high: 25, label: 'Extremely Poor'},
                {low: 26, high: 50, label: 'Very Poor'},
                {low: 51, high: 65, label: 'Poor'},
                {low: 66, high: 75, label: 'Average'},
                {low: 76, high: 85, label: 'Above Average'},
                {low: 86, high: 90, label: 'Great'},
                {low: 91, high: 100, label: 'Excellent'}
            ]
        }
    },

    computed: {
        lastRun: function() {
            if (this.program.last_run) {
                return moment(this.program.last_run).fromNow();
            }
        }
    },

    methods: {
        disableUi: function() {
            $('#program-details .btn').addClass('disabled');
        },

        enableUi: function() {
            $('#program-details .btn').removeClass('disabled');
        },

        getProgramPk: function() {
            if (!$.isEmptyObject(this.program)) {
                return this.program.id;
            }

            var pkHolder = $('#program-pk-holder');

            if (pkHolder.length) {
                return pkHolder.data('pk');
            }
        },

        fetch: function() {
            var self = this;

            $.ajax({
                url: '/api/program/' + self.getProgramPk() + '/',
                method: 'GET',
                success: function(data, text_status, jqXHR) {
                    self.$set('program', data);
                    self.$nextTick(self._onProgramSet);
                }
            });
        },

        _onProgramSet: function() {
            if (this.gage.originalValue != this.program.current_quality_score.score) {
                this._setupGage();
            }
            this._setupTagit();

            if (this.selectedReportType == 'scoreOverTime') {
                this._setupQotChart();
            }

            if (this.program.status == 'RUN') {
                if (!this.fetchInterval) {
                    this.gage = {};
                    this.fetchInterval = setInterval(this.fetch, 3000);
                }
            }

            if (this.fetchInterval && this.program.progress == 100 &&
                this.program.current_activity_description == null) {
                clearInterval(this.fetchInterval);
                this.fetchInterval = null;
            }
        },

        _setupGage: function() {
            var gageEl = $('#gage');

            if (gageEl.length) {
                gageEl.html('');
                this.gage = new JustGage({
                    id: 'gage',
                    value: this.program.current_quality_score.score || 0,
                    min: 0,
                    max: 100,
                    levelColors: ["#FF3300", "#FF9900", "#FFFF00", "#33CC33"],
                    label: this._getGageLabel()
                });
            }
        },

        _getGageLabel: function() {
            var self = this;

            if ($.isEmptyObject(self.program)) {
                return;
            }

            var label;
            $.each(this.scoreRanges, function (index, range) {
                if (self.program.current_quality_score.score >= range.low
                    && self.program.current_quality_score.score <= range.high) {
                    label = range.label;
                    return false;
                }
            });
            return label;
        },

        _onReportChange: function() {
            if (this.selectedReportType == 'scoreOverTime') {
                this.$nextTick(this._setupQotChart);
            } else if (this.selectedReportType == 'snapshot') {
                this.$nextTick(this._setupGage);
            }
        },

        _setupQotChart: function() {
            if (!this.program.quality_scores.length || !$('#canvas').length) {
                return;
            }

            var self = this, labels = [], data = [];

            $.each(self.program.quality_scores, function (index, value) {
                labels.push(moment(value.created).calendar());
                data.push(value.score);
            });

            $('#canvas').replaceWith('<canvas id="canvas" height="600" width="450"></canvas>');

            var barChartData = {
                labels: labels,
                datasets: [
                    {
                        label: "Quality score over time",
                        fillColor: "rgba(220,220,220,0.2)",
                        strokeColor: "rgba(220,220,220,1)",
                        pointColor: "rgba(220,220,220,1)",
                        pointStrokeColor: "#fff",
                        pointHighlightFill: "#fff",
                        pointHighlightStroke: "rgba(220,220,220,1)",
                        data: data
                    }
                ]
            };

            var ctx = document.getElementById("canvas").getContext("2d");

            window.qotBar = new Chart(ctx).Bar(barChartData, {
                //responsive: true,
            });
        },

        _setupTagit: function() {
            $('#program-tags').tagit({
                allowSpaces: true,
                placeholderText: 'insert, your, tags',
                afterTagRemoved: this._updateTags,
                afterTagAdded: this._updateTags
            });
        },

        _updateTags: function(event, ui) {
            if (ui.duringInitialization) {
                return;
            }

            var self = this;

            $.ajax({
                url: '/program_set_tags/',
                method: 'GET',
                data: {
                    pk: this.getProgramPk(),
                    tags: $('#program-tags').val()
                },
                success: function(data, text_status, jqXHR) {
                    self.fetch();
                }
            });
        },

        _processProgramAction: function(actionUrl) {
            var self = this;

            self.disableUi();

            $.ajax({
                url: actionUrl,
                method: 'GET',
                success: function(data, text_status, jqXHR) {
                    self.$set('program', data);
                    self.$nextTick(self._onProgramSet);
                    self.enableUi();
                }
            });
        },
        
        editSettings: function (autorun) {
            window.location = '/select_actions/' + this.getProgramPk() + (!!autorun ? '#run' : '');
        },

        setDataOrigin: function(event) {
          $.ajax({
            url: '/program/' + this.getProgramPk() + '/data_origin/',
            method: 'GET',
            data: {
              'data_origin': event.target.value,
            }
          });
        },

        setSchedule: function(event) {
          var data = {};
          $.each($(event.target).closest('form').serializeArray(), function () {
            data[this.name] = this.value;
          });
          $.ajax({
            url: '/program/' + this.getProgramPk() + '/schedule/',
            method: 'GET',
            data: data,
          });
        },
        
        renameProgram: function() {
            var self = this;

            $.ajax({
                url: '/program/' + this.getProgramPk() + '/rename/',
                method: 'GET',
                data: {
                    name: $('#program-name-input').val()
                },
                success: function(data, text_status, jqXHR) {
                    self.$set('editNameMode', false);
                    self.$set('program', data);
                    self.$nextTick(self._onProgramSet);
                }
            });
        }
    },

    ready: function () {
        var self = this;

        self.fetch();

        $('#program-name-contenteditable').on('blur', function(e) {
            self.renameProgram();
        });

        if (window.location.hash == '#run') {
            window.location.hash = ' ';
            this._processProgramAction('/program/' + this.getProgramPk() + '/optimize/');
        }
        
        $('#id_schedule_hour').timepicker({
          step: 15,
          forceRoundTime: true,
          scrollDefault: 'now',
        });
        $('#id_schedule_hour').on('change', function (event) {
          this.latest_valid_schedule_hour = event.target.value;
        });
        $('#id_schedule_hour').timepicker('setTime', new Date()).change();
        $('#id_schedule_hour').on('timeFormatError', function (event) {
          $(this).val(this.latest_valid_schedule_hour);
        });


    }
});


var ProgramTypeSelectionComponent = Vue.extend({
    template: '#program-type-selection',
    props: ['passed'],

    data: function() {
        return {
            downloadJobStarted: null,
            downloadDbJobPk: null,
            newProgramPk: null
        }
    },

    methods: {
        checkDownloadDbJob: function() {
            var self = this;
            job_is_finished(self.downloadDbJobPk, function () {
                var programBuilderUrl = '/batch_select/?pk=' + self.newProgramPk;
                self.downloadDbJobPk = null;
                self.newProgramPk = null;
                window.location.replace(programBuilderUrl);
            });
            setTimeout(self.checkDownloadDbJob, 1000);
        },
        onDbClick: function(e) {
            var self = this;

            $('#new-program-modal-body-row').hide();
            $('#new-program-modal-spinner').show();

            $.ajax({
                url: '/download_database/',
                method: 'GET',
                success: function(data, text_status, jqXHR) {
                    self.downloadJobStarted = true;
                    self.downloadDbJobPk = data.job_pk;
                    self.newProgramPk = data.program_pk;
                    self.checkDownloadDbJob();
                }
            });
        },
        onListImportClick: function(e) {
            this.$dispatch('view-change', 'list-import-dropzone');
        }
    },

    ready: function () {
        var self = this;

        $('#newProgramModal').on('hide.bs.modal', function (e) {
            if (self.downloadJobStarted) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return;
            }
            $('#new-program-modal-body-row').show();
            $('#new-program-modal-spinner').hide();
        });
    }
});


var ListImportDropzoneComponent = Vue.extend({
    template: '#list-import-dropzone',
    props: ['passed'],

    ready: function() {
        var self = this,
            container = $(this.$el),
            input = container.find(':input'),
            dropzone = container.find('#dropzone');

        dropzone.click(function(){
            input.click();
        });

        input.fileupload({
            dropZone: dropzone,
            dataType: 'json',
            forceIframeTransport: true,
            done: function(e, data) {
                var response = data.response().result;
                window.location.replace(response.redirect_url);
            }
        });
    }
});


var CreateProgramModalComponent = Vue.extend({

    data: function() {
        return {
            title: 'Create a New Data Task',
            currentView: 'program-type-selection',
            currentViewProps: {},
        }
    },

    components: {
        'program-type-selection': ProgramTypeSelectionComponent,
        'list-import-dropzone': ListImportDropzoneComponent
    },

    events: {
        'view-change': function (viewName, viewProps) {
            this.currentViewProps = viewProps || {};
            this.$set('currentView', viewName);
        },

        eventReceived: function(event) {
            // re-broadcast to child components
            this.$broadcast('eventReceived', event);
        }
    },

    ready: function () {
        var self = this;

        $('#newProgramModal').on('hidden.bs.modal', function (e) {
            self.$set('currentView', 'program-type-selection');
        });
    }

});


// Program List component
var ProgramListComponent = Vue.extend({

    replace: false,

    data: function() {
        return {
            programItems: [],
            nameFilter: '',
            statusFilter: 'active'
        }
    },

    watch: {
        'nameFilter': function (val, oldVal) {
            this.fetchPrograms();
        },
        'statusFilter': function (val, oldVal) {
            this.fetchPrograms();
        }
    },

    events: {
        eventReceived: function(event) {
            if ( ! event.program_changed)
                return;

            var self = this, consumeEvents = [];

            event.program_changed.forEach(function(e){
                var item = e.event_data.data;

                var index = self.programItems.map(function(i) { return i.id; }).indexOf(item.id);

                if (index > -1) {
                    self.programItems.splice(index, 1, item);
                }
                else {
                    self.programItems.push(item);
                }

                consumeEvents.push(e.event_id);
            });

            this.$dispatch('markConsumed', consumeEvents);
        }
    },

    ready: function() {
        this.fetchPrograms();
    },

    computed: {
        visibleProgramsCount: function() {
            var self = this, count = 0;

            this.programItems.forEach(function(item){
                if (self.isVisible(item)) {
                    count += 1;
                }
            });

            return count;
        }
    },

    methods: {
        fetchPrograms: function() {
            var self = this;

            $.ajax({
                url: '/api/program/',
                method: 'GET',
                data: {
                    nameFilter: self.nameFilter,
                    statusFilter: self.statusFilter
                },
                success: function(data, text_status, jqXHR) {
                    self.$set('programItems', data);
                }
            });
        },

        isVisible: function(item) {
            return (item.status == this.statusFilter) || (item.status != 'ARCH' && this.statusFilter == 'active');
        },

        showEdit: function(item) {
            return /COMPL|CANCEL/.test(item.status);
        },

        showCancel: function(item) {
            return /RUN|ACT|PEND/.test(item.status);
        },

        showRestart: function(item) {
            return /PAUSE|ERROR/.test(item.status);
        },

        showArchive: function(item) {
            return /ERROR|COMPL|CANCEL/.test(item.status);
        },

        getFormattedDate: function(dateString) {
            return moment(dateString).format('MMM Do YYYY, h:mm a');
        },

        getStatusIcon: function(item) {
            var icons = {
                'ACT': 'fa-bolt',
                'CREA': 'fa-file-o',
                'RUN': 'fa-circle-o-notch fa-spin',
                'PEND': 'fa-circle-o-notch fa-spin',
                'PAUSE': 'fa-pause',
                'ERROR': 'fa-exclamation-triangle',
                'COMPL': 'fa-check',
                'CANCEL': 'fa-times-circle',
                'ARCH': 'fa-archive'
            };

            return icons[item.status];
        },

        getLabelType: function(item) {
            var labels = {
                'ACT': 'warning',
                'CREA': 'primary',
                'RUN': 'primary',
                'PEND': 'primary',
                'PAUSE': 'default',
                'ERROR': 'danger',
                'COMPL': 'success',
                'CANCEL': 'danger',
                'ARCH': 'default'
            };

            return labels[item.status];
        },

        processProgramAction: function(url) {
            var self = this;

            $.ajax({
                url: url,
                method: 'GET',
                success: function(data, text_status, jqXHR) {
                    self.fetchPrograms();
                }
            });
        },

        isEmptyObject: function(obj) {
            return $.isEmptyObject(obj);
        }
    }

});


// Notification component
var Notification = Vue.extend({

    data: function() {
        return {
            showModal: false,

            currentNotification: {
                subject: '',
                text: '',
                event: {
                    id: 0
                }
            }
        }
    },

    computed: {
        modalClass: function() {
            return this.showModal ? 'in' : '';
        },

        modalDisplay: function() {
            return this.showModal ? 'block' : 'none';
        }
    },

    methods: {
        showNotification: function() {
            // show modal
            this.showModal = true;

            // mark consumed
            if (this.currentNotification.event.id > 0) {
                this.$dispatch(
                    'markConsumed', [this.currentNotification.event.id]);
            }
        }
    }

});


// Notification list
var NotificationListComponent = Notification.extend({

    replace: false,

    data: function() {
        return {
            eventRefs: {} // store reference between events and notifications
        }
    },

    events: {
        eventReceived: function(event) {
            if ( ! event.notification)
                return;

            var self = this;

            event.notification.forEach(function(e){
                self.eventRefs[e.event_data.id] = e.event_id;
            });
        }
    },

    methods: {
        showNotificationItem: function(subject, text, id) {
            this.currentNotification = {
                'subject': subject,
                'text': text,
                'event': {
                    'id': this.eventRefs[id] || 0
                }
            };

            this.showNotification();
        },

        archiveNotification: function(id) {
            $.ajax({
                url: '/notifications/archive_notification/',
                data: {'pk': id},
                success: function (data, text_status, jqXHR) {
                    if (data['result'] == 'success') {
                        var bloop = true;
                        var cid = data['notification'].id;
                        $("#notification_table").find("tr").each(function(){
                            if ( bloop ) {
                                var notification_id = $(this).attr('notificationid');
                                if (notification_id == cid) {
                                    $(this).remove();
                                    bloop = false;
                                }
                            }
                        });
                    }
                }
            });
        }
    }

});


// Notification bar component
var NotificationBarComponent = Notification.extend({

    replace: false,

    ready: function() {
        $(this.$el).show();
    },

    data: function() {
        return {
            notifications: [],
            shownNotifications: {}
        }
    },

    computed: {
        unread: function() {
            var total = this.notifications.length;

            // shownNotifications is an auxiliary object that holds
            // read notifications, so we can have a real-time count
            // before the server consumes the mark-read event:
            //
            // (total notifications - shown notifications)
            for (var key in this.shownNotifications) {
                if (this.shownNotifications.hasOwnProperty(key)) {
                    total -= 1;
                }
            }

            return total;
        }
    },

    events: {
        eventReceived: function(event) {
            var notifications = [];

            if (event.notification) {
                event.notification.forEach(function(e){
                    notifications.push({
                        subject: e.event_data.subject,
                        text: e.event_data.text,
                        event: {
                            id: e.event_id
                        }
                    });
                });
            }

            this.notifications = notifications;
        }
    },

    methods: {
        showNotificationByIndex: function(index) {
            this.currentNotification = this.notifications[index];
            this.shownNotifications[this.currentNotification.event.id] = true;
            this.showNotification();
        }
    }

});


new Vue({
    el: 'body',

    props: ['consumeEvents'],

    data: function() {
        return {
            // events marked as consumed
            consumedEvents: [],

            // fetch call options
            fetchDelay: 5000,
            fetchTimeout: null,
            fetchActive: false
        }
    },

    components: {
        'program-list': ProgramListComponent,

        'notification-list': NotificationListComponent,
        'notification-bar': NotificationBarComponent,

        'create-program-modal': CreateProgramModalComponent,
        'program-details': ProgramDetailsComponent
    },

    ready: function() {
        this.fetchData();
    },

    events: {
        fetchData: function() {
            if (this.fetchActive)
                return;

            var self = this, delay = 5000;

            // block fetch
            this.fetchActive = true;

            // recursive
            clearTimeout(this.fetchTimeout);

            // consumedEvents
            var consumedEvents = [];
            while (this.consumedEvents.length > 0)
                consumedEvents.push(this.consumedEvents.pop());

            $.ajax({
                url: '/events.json',
                data: {
                    'consume_events': this.consumeEvents,
                    'consumed_events': consumedEvents.join(',')
                },
                dataType: 'json',
                success: function(data) {
                    // notify components
                    self.$broadcast('eventReceived', data);
                },
                complete: function() {
                    self.fetchActive = false;
                    self.fetchTimeout = setTimeout(function(){
                        self.$emit('fetchData');
                    }, self.fetchDelay);
                }
            });
        },

        markConsumed: function(eventIds) {
            for (var i = 0; i < eventIds.length; ++i)
                this.consumedEvents.push(eventIds[i]);

            this.$emit('fetchData');
        }
    },

    methods: {
        fetchData: function() {
            this.$emit('fetchData');
        },
    }
});
