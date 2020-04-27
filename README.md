# Splunk-TA for WebEx Meetings

> The **Splunk-TA for Webex Meetings** uses the _Webex Meetings XML API_ to fetch data and ingest it into Splunk.

[![HitCount](http://hits.dwyl.com/splunk/ta-webex-meetings-add-on-for-splunk.svg)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/releases)
[![GitHub issues](https://img.shields.io/github/issues/splunk/ta-webex-meetings-add-on-for-splunk?label=issues&color=informational)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/issues)
[![GitHub All Releases](https://img.shields.io/github/downloads/splunk/ta-webex-meetings-add-on-for-splunk/total?label=download&logo=github&style=flat-square&color=important)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/releases)
[![Add-on Builder](https://img.shields.io/badge/built%20with-AoB%20/%20Python3-ff69b4.svg)](https://docs.splunk.com/Documentation/AddonBuilder/3.0.1/UserGuide/Whatsnew)

## Getting Started
This is a TA to pull in data from WebEx Meetings XML API.
These [API endpoints](https://developer.cisco.com/docs/webex-xml-api-reference-guide/#!lstmeetingusagehistory) are being hit to fetch data for the meetings.

| XML API                   | Sourcetype                                          | Splunk Time Field | Type            | Recommended Interval |
|---------------------------|-----------------------------------------------------|-------------------|-----------------|----------------------|
| LstmeetingattendeeHistory | cisco:webex:meetings:history:meetingattendeehistory | joinTime          | Historical      | >= 86400             |
| LstmeetingusageHistory    | cisco:webex:meetings:history:meetingusagehistory    | meetingStartTime  | Historical      | >= 86400             |
| LsteventsessionHistory    | cisco:webex:meetings:history:eventsessionhistory    | sessionStartTime  | Historical      | >= 86400             |
| LstrecordaccessHistory    | cisco:webex:meetings:history:recordaccesshistory    | creationTime      | Historical      | >= 86400             |
| LstsupportsessionHistory  | cisco:webex:meetings:history:supportsessionhistory  | sessionStartTime  | Historical      | >= 86400             |
| LsttrainingsessionHistory | cisco:webex:meetings:history:trainingsessionhistory | sessionStartTime  | Historical      | >= 86400             |
| LstsummarySession         | cisco:webex:meetings:general:summarysession         | actualStartTime   | Active Sessions | <= 60                |


**DISCLAIMER**: Guidance from Cisco states historical data retrieval may be incomplete if fetched less than 48 hours from time meetings ended. Therefore it's recommended to set the interval to 86400 or more for historical input.

#### Create a Service Account

Create the service account in **Webex Meetings site's admin portal** (CompanyXYZ.webex.com).  Attached is the sample Screenshots.  Once the API user was created it was linked to the Control Hub because we have linked sites.

Based on which Webex you have, the account creation might be different.

If you have to go to admin.webex.com (Control Hub) to login and manage your webex account, you may run into some issues.  Generally, Webex Teams and Webex Meetings portal are completely automated from Active directory connector and adding a **local user** is **DISABLED** as soon as AD connector is set up.

If you do not have any automation enabled, you should be able to create a user, you will have to assign a license to the user and then give the user partial **Site Admin** read-only rights.

If you are managing the site from **Control Hub**, please take a look at this link it should help.

Alternatively, [Add-Users-Manually-in-Cisco-Webex-Control-Hub ](https://help.webex.com/en-us/v71ztb/Add-Users-Manually-in-Cisco-Webex-Control-Hub ) can also be a workaround if you have AD Connector setup as well.

<img src="appserver/static/img/Add%20User.png"  width="600" height="450">


#### Installation and Configuration Steps
This application can be installed on-prem and cloud.

##### Installation Steps for `on-prem`
Install the TA on one of the Heavy Forwarder(s).

##### Installation Steps for `cloud`
Create a support ticket with `APP-CERT` reference to get it installed on the Cloud instance *OR* follow the cloud-ops steps to install non-published applications.

#### Configuration steps
The configuration steps are common for `on-prem` and `cloud`. Please follow the following steps in order:
1. Open the Web UI for the Heavy Forwarder (or IDM).
2. Access the TA from the list of applications.
3. Set global setings.
- Click on `Configuration` button on the top left corner.
- Click on `Add-on Settings` button.
- Enter the following details:
  - **Site Name** (_required_): This identifies the Webex site you are targeting with your add-on. For example, if the URL is `https://splunk.webex.com`, the Webex Site that you have to enter is `splunk`.
  - **Username** (_required_): Service Account Username or E-mail address of the host or admin account making the request. For example: `splunker@splunk.com`.
  - **Password** (_required_): Password of the account associated with the e-mail address above. The password will be masked.
- Click on the `Save` green button.
4. Create input for active scheduled sessions .
- Click on `Inputs` button on the top left corner.
- Click on `Create New Input` button on the top right corner.
- Select `General Service`
- Enter the following details in the pop up box:
    - **Name** (_required_): Unique name for the data input.
    - **Interval** (_required_): Time interval of input in seconds. **Note**: Interval should be 60 or less for general service session data.
    - **Index** (_required_): Index for storing data.
    - **Monitor Active Session**: Please make sure `Monitor Active Session` is checked.
- Click on the `Add` green button on the bottom right of the pop up box.
 5. Create input for historical meetings.
 - Click on `Inputs` button on the top left corner.
 - Click on `Create New Input` button on the top right corner.
 - Select `History Service`
 - Enter the following details in the pop up box:
    - **Name** (_required_): Unique name for the data input.
    - **Interval** (_required_): Time interval of input in seconds. **Note**: Interval should be 86400 (24 hours) or more for historical data
    - **Index** (_required_): Index for storing data.
    - **Endpoints** (_required_): Historical endpoints that are used to fetch historical data back.
    - **Begin Time** (_required_): This is the time from where you want to ingest the historical data. Please enter UTC time. Format: `MM/DD/YYYY hh:mm:ss` **NOTE**: Begin Date must be at least 3 days ago and ideally no more than 90 days.
- Click on the `Add` green button on the bottom right of the pop up box.

## Example(s)

## Global Setting
<img src="appserver/static/img/global_setting.png"  width="600" height="450">

### Input type: Scheduled Active Session 

<img src="appserver/static/img/general_service_1.png"  width="1500" height="150">
<img src="appserver/static/img/general_service_2.png"  width="600" height="450">

### Input type: Historical Meetings

<img src="appserver/static/img/history_service_1.png"  width="1500" height="150">
<img src="appserver/static/img/history_service_2.png"  width="600" height="450">



## Credits & Acknowledgements (optional)
> Built by Splunk's FDSE Team (#team-fdse). 
