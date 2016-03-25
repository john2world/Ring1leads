  connection:
    {
    type:'salesforce',
    username:'joe@datasidekick.com',
    token:'xyzxyz',
    idUrl:'na13.salesforce.com'
    },
  table_filter:
    {
      table: 'Lead'
    },
  filters:
    {
      'CreatedDate < 2013.11.01',
      'Status = 'Open',
    }
  dupmatchrules:
    {
      'Email must match exactly',
      'Last name must be very similar',   <- NEED TO FIGURE OUT SYNTAX
    }
  survivingrecordrules:
    {
      {priority:1, 'sales_ready__c = True'},
      {priority:2, 'ORDERBY LastModifiedDate'},
    }
  survivingvaluerules:
    {
      {LeadSource ORDERBY CreatedDate},
    }


============

utils.django_model_instance_to_json output with depth=1:

{
  "status": "CREA",
  "read_only": false,
  "program_ptr":
      {
        "status": "CREA",
        "read_only": false,
        "id": 1,
        "name": "Dreamforce 2015"
        },
  "name": "Dreamforce 2015",
  "dupmatchrule_set": [],
  "table_schema": {"id": 1, "name": "Lead"},
  "report_set": [],
  "survivingrecordrule_set":
      [
        {
          "priority": 1,
          "id": 1,
          "rule": "NEWEST"
        },
        {
          "priority": 2,
          "id": 2,
          "rule": "NEWEST"
        }
      ],
    "fieldfilter_set":
      [
        {
          "operator": "DATEBEFORE",
          "field_value": "2013.11.01",
          "id": 1
        }
      ],
    "user":
      {
        "first_name": "Joe",
        "last_name": "Fusaro",
        "is_active": true,
        "email": "josephmfusaro@gmail.com",
        "is_first_login": true,
        "last_login": "2015-11-27T16:44:02.647125+00:00",
        "mobile_number": null,
        "is_admin": true,
        "password": "pbkdf2_sha256$20000$Z0XlaxwLl0Ta$nzxVsLdaiTZ2q72ctM5nPQTQTQh6EiSZYCg6t0Gv0g4=",
        "id": 1
      },
    "qualityscore_set": [],
    "survivingvaluerule_set":
      [
        {
          "id": 1,
          "rule": "ADD"
        },
        {
          "id": 2,
          "rule": "OLDEST"
        }
      ],
    "tablefilter_set": [],
    "id": 1,
    "polymorphic_ctype":
      {
        "model": "batchprogram",
        "id": 23,
        "app_label": "program_manager"
      }
    }


with depth=2:

{
  "status": "CREA",
  "read_only": false,
  "program_ptr":
  {
    "batchprogram":
    {
      "status": "CREA",
      "read_only": false,
      "id": 1,
      "name": "Dreamforce 2015"
    },
    "status": "CREA",
    "name": "Dreamforce 2015",
    "table_schema":
    {
      "id": 1,
      "name": "Lead"
    },
    "read_only": false,
    "user":
    {
      "first_name": "Joe",
      "last_name": "Fusaro",
      "is_active": true,
      "email": "josephmfusaro@gmail.com",
      "is_first_login": true,
      "last_login": "2015-11-27T23:41:51.223426+00:00",
      "mobile_number": null,
      "is_admin": true,
      "password":"pbkdf2_sha256$20000$HJHHWBawgVES$hanL4VjQXiAMnqBQ/8noruurl+NDS7wPf1TP/2Z2erI=",
      "id": 1
    },
    "qualityscore_set":
    [
      {
        "percent_spam_email": null,
        "avg_age": null,
        "created": "2015-11-27T23:42:47.227273+00:00",
        "avg_since_last_modified": null,
        "percent_valid_location": null,
        "percent_valid_phone": null,
        "score": 45,
        "percent_valid_email": null,
        "percent_complete": null,
        "id": 1
      },
      {
        "percent_spam_email": null,
        "avg_age": null,
        "created": "2015-11-27T23:42:47.228395+00:00",
        "avg_since_last_modified": null,
        "percent_valid_location": null,
        "percent_valid_phone": null,
        "score": 69,
        "percent_valid_email": null,
        "percent_complete": null,
        "id": 2
      },
      {
        "percent_spam_email": null,
        "avg_age": null,
        "created": "2015-11-27T23:42:47.229648+00:00",
        "avg_since_last_modified": null,
        "percent_valid_location": null,
        "percent_valid_phone": null,
        "score": 75,
        "percent_valid_email": null,
        "percent_complete": null,
        "id": 3
      },
      {
        "percent_spam_email": null,
        "avg_age": null,
        "created": "2015-11-27T23:42:47.231058+00:00",
        "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 89, "percent_valid_email": null, "percent_complete": null, "id": 4}, {"percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.232180+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 97, "percent_valid_email": null, "percent_complete": null, "id": 5}, {"percent_spam_email": 0, "avg_age": 49, "created": "2015-11-27T23:42:47.233255+00:00", "avg_since_last_modified": 10, "percent_valid_location": 68, "percent_valid_phone": 87, "score": 82, "percent_valid_email": 96, "percent_complete": 92, "id": 6}], "id": 1, "polymorphic_ctype": {"model": "batchprogram", "id": 23, "app_label": "program_manager"}}, "name": "Dreamforce 2015", "dupmatchrule_set": [], "table_schema": {"externaltable_ptr": {"id": 1, "name": "Lead"}, "fields": [], "oauthtoken": {"password": "", "access_token": "", "id_token": "", "id_url": "", "salesforce_user_id": "", "salesforce_organization_id": "", "thumbnail_photo": "", "is_sandbox": false, "issued_at": null, "instance_url": "", "active": false, "id": 1, "refresh_token": ""}, "polymorphic_ctype": {"model": "salesforcetable", "id": 19, "app_label": "salesforce"}, "id": 1, "program_set": [{"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}], "name": "Lead"}, "survivingrecordrule_set": [], "fieldfilter_set": [], "user": {"first_name": "Joe", "last_name": "Fusaro", "logentry_set": [{"action_flag": 2, "action_time": "2015-11-28T00:35:57.808809+00:00", "object_repr": "Dreamforce 2015", "object_id": "1", "change_message": "Changed table_schema. Changed score, percent_valid_location, percent_valid_phone, percent_valid_email, percent_spam_email, percent_complete, avg_age and avg_since_last_modified for quality score \\"82 | Dreamforce 2015\\".", "id": 7}, {"action_flag": 1, "action_time": "2015-11-28T00:34:47.946268+00:00", "object_repr": "Lead", "object_id": "1", "change_message": "", "id": 6}, {"action_flag": 1, "action_time": "2015-11-28T00:34:37.810417+00:00", "object_repr": "josephmfusaro@gmail.com", "object_id": "1", "change_message": "", "id": 5}, {"action_flag": 1, "action_time": "2015-11-28T00:17:13.000757+00:00", "object_repr": "Dreamforce 2015", "object_id": "1", "change_message": "", "id": 4}, {"action_flag": 2, "action_time": "2015-11-27T23:59:19.333850+00:00", "object_repr": "Report object", "object_id": "1", "change_message": "No fields changed.", "id": 3}, {"action_flag": 2, "action_time": "2015-11-27T23:57:51.739122+00:00", "object_repr": "Report object", "object_id": "1", "change_message": "No fields changed.", "id": 2}, {"action_flag": 1, "action_time": "2015-11-27T23:55:10.879252+00:00", "object_repr": "Report object", "object_id": "1", "change_message": "", "id": 1}], "is_active": true, "report_set": [{"id": 1}], "email": "josephmfusaro@gmail.com", "is_first_login": true, "oauthtokens": [{"password": "", "access_token": "", "id_token": "", "id_url": "", "salesforce_user_id": "", "salesforce_organization_id": "", "thumbnail_photo": "", "is_sandbox": false, "issued_at": null, "instance_url": "", "active": false, "id": 1, "refresh_token": ""}], "mobile_number": null, "is_admin": true, "last_login": "2015-11-27T23:41:51.223426+00:00", "password": "pbkdf2_sha256$20000$HJHHWBawgVES$hanL4VjQXiAMnqBQ/8noruurl+NDS7wPf1TP/2Z2erI=", "id": 1, "program_set": [{"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}]}, "qualityscore_set": [{"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.227273+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 45, "percent_valid_email": null, "percent_complete": null, "id": 1}, {"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.228395+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 69, "percent_valid_email": null, "percent_complete": null, "id": 2}, {"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.229648+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 75, "percent_valid_email": null, "percent_complete": null, "id": 3}, {"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.231058+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 89, "percent_valid_email": null, "percent_complete": null, "id": 4}, {"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": null, "avg_age": null, "created": "2015-11-27T23:42:47.232180+00:00", "avg_since_last_modified": null, "percent_valid_location": null, "percent_valid_phone": null, "score": 97, "percent_valid_email": null, "percent_complete": null, "id": 5}, {"program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "percent_spam_email": 0, "avg_age": 49, "created": "2015-11-27T23:42:47.233255+00:00", "avg_since_last_modified": 10, "percent_valid_location": 68, "percent_valid_phone": 87, "score": 82, "percent_valid_email": 96, "percent_complete": 92, "id": 6}], "report": {"user": {"first_name": "Joe", "last_name": "Fusaro", "is_active": true, "email": "josephmfusaro@gmail.com", "is_first_login": true, "last_login": "2015-11-27T23:41:51.223426+00:00", "mobile_number": null, "is_admin": true, "password": "pbkdf2_sha256$20000$HJHHWBawgVES$hanL4VjQXiAMnqBQ/8noruurl+NDS7wPf1TP/2Z2erI=", "id": 1}, "batch_program": {"status": "CREA", "read_only": false, "id": 1, "name": "Dreamforce 2015"}, "id": 1, "qualityscorereport": {"id": 1}}, "survivingvaluerule_set": [], "tablefilter_set": [], "id": 1, "polymorphic_ctype": {"model": "batchprogram", "logentry_set": [{"action_flag": 2, "action_time": "2015-11-28T00:35:57.808809+00:00", "object_repr": "Dreamforce 2015", "object_id": "1", "change_message": "Changed table_schema. Changed score, percent_valid_location, percent_valid_phone, percent_valid_email, percent_spam_email, percent_complete, avg_age and avg_since_last_modified for quality score \\"82 | Dreamforce 2015\\".", "id": 7}], "id": 23, "permission_set": [{"codename": "add_batchprogram", "id": 67, "name": "Can add batch program"}, {"codename": "change_batchprogram", "id": 68, "name": "Can change batch program"}, {"codename": "delete_batchprogram", "id": 69, "name": "Can delete batch program"}], "app_label": "program_manager"}}'
