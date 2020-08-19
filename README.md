# Cisco WebEx Meetings Add-on for Splunk

> The **Cisco WebEx Meetings Add-on for Splunk** uses the _Webex Meetings XML API_ to fetch data and ingest it into Splunk.

[![HitCount](http://hits.dwyl.com/splunk/ta-webex-meetings-add-on-for-splunk.svg)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/releases)
[![GitHub issues](https://img.shields.io/github/issues/splunk/ta-webex-meetings-add-on-for-splunk?label=issues&color=informational)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/issues)
[![GitHub All Releases](https://img.shields.io/github/downloads/splunk/ta-webex-meetings-add-on-for-splunk/total?label=download&logo=github&style=flat-square&color=important)](https://github.com/splunk/ta-webex-meetings-add-on-for-splunk/releases)
[![Add-on Builder](https://img.shields.io/badge/built%20with-Python3-ff69b4.svg)](https://docs.splunk.com/Documentation/AddonBuilder/3.0.1/UserGuide/Whatsnew)
[![ThirdPartyCredits](https://img.shields.io/badge/Thirdparty%20Credits-Addon%20Builder-purple.svg)](https://docs.splunk.com/Documentation/AddonBuilder/3.0.1/UserGuide/Thirdpartysoftwarecredits)


## Getting Started
This is a TA to pull in data from Cisco WebEx Meetings XML API.
These [API endpoints](https://developer.cisco.com/docs/webex-xml-api-reference-guide/#!lstmeetingusagehistory) are being hit to fetch data for the meetings.

| XML API                    | Sourcetype                                           | Splunk Time Field | Type            | Recommended Interval |
|----------------------------|------------------------------------------------------|-------------------|-----------------|----------------------|
| LsttrainingattendeeHistory | cisco:webex:meetings:history:trainingattendeehistory | startTime         | Historical      | >= 86400             |
| LstsupportattendeeHistory  | cisco:webex:meetings:history:supportattendeehistory  | startTime         | Historical      | >= 86400             |
| LsteventattendeeHistory    | cisco:webex:meetings:history:eventattendeehistory    | startTime         | Historical      | >= 86400             |
| LstmeetingattendeeHistory  | cisco:webex:meetings:history:meetingattendeehistory  | joinTime          | Historical      | >= 86400             |
| LstmeetingusageHistory     | cisco:webex:meetings:history:meetingusagehistory     | meetingStartTime  | Historical      | >= 86400             |
| LsteventsessionHistory     | cisco:webex:meetings:history:eventsessionhistory     | sessionStartTime  | Historical      | >= 86400             |
| LstrecordaccessHistory     | cisco:webex:meetings:history:recordaccesshistory     | creationTime      | Historical      | >= 86400             |
| LstsupportsessionHistory   | cisco:webex:meetings:history:supportsessionhistory   | sessionStartTime  | Historical      | >= 86400             |
| LsttrainingsessionHistory  | cisco:webex:meetings:history:trainingsessionhistory  | sessionStartTime  | Historical      | >= 86400             |
| LstsummarySession          | cisco:webex:meetings:general:summarysession          | actualStartTime   | Active Sessions | <= 60                |


**DISCLAIMER**: Guidance from Cisco states historical data retrieval may be incomplete if fetched less than 48 hours from time meetings ended. Therefore it's recommended to set the interval to 86400 or more for historical input.

#### Create a Service Account

Create the service account in **Webex Meetings site's admin portal** (CompanyXYZ.webex.com).    Once the API user was created it was linked to the Control Hub because we have linked sites.

Based on which Cisco Webex Meetings you have, the account creation might be different.

If you have to go to admin.webex.com (Control Hub) to login and manage your webex account, you may run into some issues.  Generally, Webex Teams and Webex Meetings portal are completely automated from Active directory connector and adding a **local user** is **DISABLED** as soon as AD connector is set up.

If you do not have any automation enabled, you should be able to create a user, you will have to assign a license to the user and then give the user partial **Site Admin** read-only rights.

If you are managing the site from **Control Hub**, please take a look at this link it should help.

Alternatively, [Add-Users-Manually-in-Cisco-Webex-Control-Hub ](https://help.webex.com/en-us/v71ztb/Add-Users-Manually-in-Cisco-Webex-Control-Hub ) can also be a workaround if you have AD Connector setup as well.

#### Create a Webex Meetings OAuth Integration App

An integration is what you'd have to use if you have Single Sign-On (SSO) or OAuth enabled in your Webex account and you are not able to create a Service Account. This requires you to be logged in to [Cisco DevNet](https://developer.cisco.com/site/webex-integration/) using a Webex Meetings Site Admin account. The dialog prompt for logging in to DevNet has the option to Login with Webex Meetings. Please make sure you pick the `Login with Webex Meetings` option, and other log in options will not work for this purpose. After login you can create a dedicated integration app for this Add-on.
- Log in to [Cisco DevNet](https://developer.cisco.com/site/webex-integration/) using a Webex Meetings Site Admin account.
- Click on the `Add App Information` button on the top right corner.
- Enter the following details:
    - **Integration name**: Enter an integration name as you like. 
    - **Redirect URI**: The Redirect URI **MUST** follow this pattern: 
    ```http://{{hostname}}:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth```
    Please  replace the `{{hostname}}` with the hostname of the Splunk Heavy Forwarder (or IDM). For example, if the hostname of the HF or IDM is `0.0.0.0`, the Redirect URI you have to enter is:
    `http://0.0.0.0:8000/en-US/splunkd/__raw/services/cisco-webex-meetings-oauth`
- Click on the `Submit` button.
- Please copy the `Client ID` and `Client Secret` somewhere for further use.

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
If you use a Webex Service Account, please refer to [Section 3.1](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk/tree/Oauth-SSO#31-set-global-settings-for-webex-service-account) to set global settings. If you have Single Sign-On (SSO) or OAuth enabled in your Webex accout, please refer to [Section 3.2](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk/tree/Oauth-SSO#32-set-global-settings-for-ssooauth) to set global settings. 
    ###### 3.1 Set global settings for Webex Service Account
    Please refer to [Create a Service Account](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk#create-a-service-account) section to create a Sevice Account first. 
    - Click on `Configuration` button on the top left corner.
    - Click on `Add-on Settings` button.
    - Enter the following details:
      - **Site Name** (**_required_**): This identifies the Webex site you are targeting with your add-on. For example, if the URL is `https://splunk.webex.com`, the Webex Site that you have to enter is `splunk`.
      - **Username** (**_required_**): Service Account Username or E-mail address of the host or admin account making the request. For example: `splunker@splunk.com`.
      - **Authentication Type** (**_required_**): Please select `Basic Password Auth` for Webex Service Account.
      - **Hostname** (_optional_): **Please leave it blank**. (Hostname is optional for Basic Password Auth type.)
      - **Client ID** (_optional_): **Please leave it blank**. (Client ID is optional for Basic Password Auth type.) 
      - **Client Secret** (_optional_): **Please leave it blank**. (Client Secret is optional for Basic Password Auth type.) 
      - **Password / Access Token** (**_required_**): Password of the account associated with the e-mail address above. The password will be masked.
      - **Refresh Token** (_optional_): **Please leave it blank**. (Refresh Token is optional for Basic Password Auth type.) 
    - Click on the `Save` green button.
    ###### 3.2 Set global settings for SSO/OAuth
    Please refer to [Create a Webex Meetings OAuth Integration App](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk#create-a-webex-meetings-oauth-integration-app) section to create an integration app first.
    - Click on `Configuration` button on the top left corner.
    - Click on `Add-on Settings` button.
    - Enter the following details:
      - **Site Name** (**_required_**): This identifies the Webex site you are targeting with your add-on. For example, if the URL is `https://splunk.webex.com`, the Webex Site that you have to enter is `splunk`.
      - **Username** (**_required_**): Service Account Username or E-mail address of the host or admin account making the request. For example: `splunker@splunk.com`.
      - **Authentication Type** (**_required_**): Please select `OAuth/SSO` for SSO/OAuth enabled account.
      - **Hostname** (**_required_**): Please enter the hostname of the Heavy Forwarder (or IDM). (Hostname is required for SSO/OAuth type.)
      - **Client ID** (**_required_**): Please enter the Client ID of your Webex Meetings Integration App that you create for this Add-on. (Client ID is required for SSO/OAuth type.) 
      - **Client Secret** (**_required_**): Please enter the Client Secret of your Webex Meetings Integration App that you create for this Add-on. (Client Secret is required for SSO/OAuth type.)
      - **Password / Access Token** (**_required_**): To get the Access Token, please click `Generate Tokens` button under the text box. (**Note**: Please make sure you enter the correct `Client ID` and `Client Secret` at the last steps.) In the pop-up window, enter your email/username, and hit `Next`. Click the `Accept` button to grant the permissions. You should see your `Access Token` and `Refresh Token`. Copy & paste the `Access Token` here. (**Note**: If you see the error messages, e.g. "Invalid client secret", please close the pop-up window, enter the correct client secret, and re-click the `Generate Tokens` to start over it again.)
      - **Refresh Token** (**_required_**): Copy & paste the `Refresh Token` that obtained from the last step here. (Refresh Token is required for SSO/OAuth type.)
    - Click on the `Save` green button.
4. Create input for active scheduled sessions .
- Click on `Inputs` button on the top left corner.
- Click on `Create New Input` button on the top right corner.
- Select `General Service`
- Enter the following details in the pop-up box:
    - **Name** (_required_): Unique name for the data input.
    - **Interval** (_required_): Time interval of input in seconds. **Note**: Interval should be 60 or less for general service session data.
    - **Index** (_required_): Index for storing data.
    - **Monitor Active Session**: Please make sure `Monitor Active Session` is checked.
- Click on the `Add` green button on the bottom right of the pop-up box.
 5. Create input for historical meetings.
 - Click on `Inputs` button on the top left corner.
 - Click on `Create New Input` button on the top right corner.
 - Select `History Service`
 - Enter the following details in the pop-up box:
    - **Name** (_required_): Unique name for the data input.
    - **Interval** (_required_): Time interval of input in seconds. **Note**: Interval should be 86400 (24 hours) or more for historical data
    - **Index** (_required_): Index for storing data.
    - **Endpoints** (_required_): Historical endpoints that are used to fetch historical data back.
    - **Begin Time** (_required_): This is the time from where you want to ingest the historical data. Please enter UTC time. Format: `MM/DD/YYYY hh:mm:ss` **NOTE**: Begin Date must be at least 3 days ago and ideally no more than 90 days.
- Click on the `Add` green button on the bottom right of the pop-up box.
6. Set Proxy Setting (optional)
 - Click on `Configuration` button on the top left corner.
- Click on `Proxy` button.
- Enter the following details:
  - **Enable** (_required_) : Check `Enable` box if you want to enable proxy support
  - **Proxy Type** (_required_) : Select a Proxy Type: `http`, `socks4`, `socks5`.
  - **Host** (_required_) : Proxy URL.
  - **Port** (_required_) : Proxy Port.
  - **Username** : Proxy Username.
  - **Password** : Proxy Password.
  - **Remote DNS resolution** : Checkbox for enabling remote DNS resolution.
- Click on the `Save` green button.


## Troubleshooting 

- [Check Conenctivity to WebEx API via shell/curl script](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk/wiki/Troubleshooting).

## Versions Supported

  - Tested for installation and basic ingestion on 8.1.0, 8.0.1, 7.3, 7.2, and 7.0 based on Cisco WebEx Meetings test account.


> Built by Splunk's FDSE Team (#team-fdse).


## Credits & Acknowledgements

* Yuan Ling
* Joe Welsh
* Ankit Bhagat
* Sandeep Vasani
* Steven Hanna
* Mayur Pipaliya

## EOF :checkered_flag:

* Want to **contribute**? Great! Feel free to create a [PR](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk/pulls).

* **Found a :bug: bug?** [Open an issue](https://github.com/splunk/ta-cisco-webex-meetings-add-on-for-splunk/issues/new) with some [emojis](http://emoji.muan.co). Issues without emojis are not valid. :trollface:
