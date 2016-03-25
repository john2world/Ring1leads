
function hideQualityScoreData(){
    $('.progress-wrapper').show();
    $('.stats-wrapper').hide();
}

function showQualityScoreData(data){
    $('.progress-wrapper').hide();
    $('.stats-wrapper').show();

    var g = new JustGage({
      id: "gauge_" + data.program_id,
      value: data.score,
      min: 0,
      max: 100,
      levelColors : [  "#FF3300", "#FF9900", "#FFFF00",  "#33CC33" ]
    });

    for (var field in data){
        var value = data[field];
        if (value === undefined || value === null) {
            continue;
        }
        $('.qs-' + field).html(value);
        $('.qs-container-' + field).show();
    }
}

function getQualityScore(){
    $.get('/qs_data/' + qualityScoreId + '/', function(data){
        var progress = parseInt(data.progress);
        if (progress == 100 && data.score != null){ // completed
            clearInterval(getQualityScoreInterval);
            showQualityScoreData(data);
        }
        else {
            if (isNaN(progress)){
                progress = 0;
            }
            hideQualityScoreData();
            $('.progress-bar').css({width: progress + '%'});
            $('.qs-progress').html(progress);
        }
    });
}

var qualityScoreId;
var getQualityScoreInterval;


$(function(){
    $('[class^="qs-container"]').hide();
    qualityScoreId = $('#qs-id').attr('data-qs-id');
    if (qualityScoreId) {
        getQualityScore();
        getQualityScoreInterval = setInterval(getQualityScore, 1000);
    }
});
