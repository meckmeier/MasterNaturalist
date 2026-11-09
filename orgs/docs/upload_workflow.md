# Upload Process
URLS:
NOTE- due to the implementation of the federated state - implementation will use the path with the /st abbr/ to ensure that the upload goes only to organizations registered in the state you are viewing.

path("uploads/", views.upload_dashboard, name="upload_dashboard"),

path("upload/<int:upload_id>/map/", views.upload_map, name="upload_map"),

path("upload/<int:upload_id>/stage/", views.upload_stage, name="upload_stage"),

path("upload/<int:upload_id>/review_raw/", views.upload_review_raw, name="upload_review_raw"),

path("upload/<int:upload_id>/build_pending/", views.upload_build_pending, name="upload_build_pending"),

path("upload/<int:upload_id>/review_locations/", views.upload_review_locations, name="upload_review_locations"),

path("upload/<int:upload_id>/review_activities/", views.upload_review_activities, name="upload_review_activities"),

path("upload/<int:upload_id>/publish/", views.upload_publish, name="upload_publish"),

path("upload/<int:upload_id>/success/", views.upload_success, name="upload_success"),

path("upload/<int:upload_id>/cancel/", views.upload_cancel_confirm, name="upload_cancel_confirm"),

path("upload/<int:upload_id>/rollback-confirm/",views.upload_rollback_confirm,name="upload_rollback_confirm",),

path("upload/<int:upload_id>/rollback/", views.upload_rollback, name="upload_rollback"),

spath("uploads/<int:upload_id>/results/",views.upload_results,name="upload_results"),

## 1. Stage
Initiate the process: path("upload/<int:org_id>/", views.upload_csv, name="upload_csv")
views.upload_csv → call CSVImporter.read() → views.upload_map

## 2. Map columns
views.upload_map → calls all CSVImporter.read() (again), build_dropdown_options, build_default_mapping, validate_mapping → views.upload_stage

## 3. Stage data
views.upload_stage → calls CSVImporter.read(), .normalize(), .validate(), .process(). Logs in upload file. → views.upload_review_raw
SHOWS a review page where you can adjust some elements. Then proceeds to → views.upload_build_pending

## 4. Create pending records
views.upload_build_pending → calls build_pending_for_upload → views. upload_review_locations

## 5. Resolve locations
views. upload_review_locations
SHOWS a review page where you can adjust some elements. The code for doing the location merge, or skip is in this view code. On the page it will use the CONTINUE button to call the next step : views.upload_review_activities

## 6. Review
views.upload_review_activities 
SHOWS a review page where you can skip individual activities. The code for storing the skipped setting is in this view code. On the page there is a CONTINUE button that will call the next step: views.upload_publish

## 7. Publish
views.upload_publish → calls publish_pending_upload → views.upload_dashboard

## 8. Dashboard
views.upload_dashboard 
SHOWS a review page, where you can VIEW PUBLISHED activities, ROLLBACK the upload.

There are also CANCEL_UPLOAD buttons on most of the process pages.

