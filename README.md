# Splunk-TA for WebEx Meetings

> The **Splunk-TA for Webex Meetings** uses the _Webex Meetings XML API_ to fetch data and ingest it into Splunk.

## Getting Started
This is a TA to pull in data from WebEx Meetings XML API. 
These [API endpoints](https://developer.cisco.com/docs/webex-xml-api-reference-guide/#!lstmeetingusagehistory) are being hit to fetch data for the meetings. 

| XML API                   | Sourcetype                              | Time Field       | Type            | Recommended Interval |
|---------------------------|-----------------------------------------|------------------|-----------------|----------------------|
| LstmeetingattendeeHistory | cisco:webex:meetingattendeehistory:list | joinTime         | Historical      | >= 86400             |
| LstmeetingusageHistory    | cisco:webex:meetingusagehistory:list    | meetingStartTime | Historical      | >= 86400             |
| LsteventsessionHistory    | cisco:webex:eventsessionhistory:list    | sessionStartTime | Historical      | >= 86400             |
| LstrecordaccessHistory    | cisco:webex:recordaccesshistory:list    | creationTime     | Historical      | >= 86400             |
| LstsupportsessionHistory  | cisco:webex:supportsessionhistory:list  | sessionStartTime | Historical      | >= 86400             |
| LsttrainingsessionHistory | cisco:webex:trainingsessionhistory:list | sessionStartTime | Historical      | >= 86400             |
| LstsummarySession         | cisco:webex:session:list                | actualStartTime  | Active Sessions | <= 60                |


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
3. Click on `Add New Input` button on the top right corner.
4. Enter the following details:
  - **Site Name** (_required_): This identifies the Webex site you are targeting with your add-on. For example, if the URL is `https://splunk.webex.com`, the Webex Site that you have to enter is `splunk`.
  - **Username** (_required_): Service Account Username or E-mail address of the host or admin account making the request. For example: `splunker@splunk.com`.
  - **Authentication Type** (_required_): Defaults to Basic Password Auth.
  - **Password** (_required_): Password of the account associated with the e-mail address above. The password will be masked.
  - **Continuous Monitoring**: Check this when retrieving data from Live Session Endpoint. **Note:** Please leave Historical Endpoints and Begin Time as blank 
  - **Historical Endpoints** : Use this when retrieving data from Historical Endpoints. **Note:** Please specify a Begin Time below and do not check the Continuous Monitoring checkbox.
  - **Begin Time**: This is the timeframe starting from where you want to ingest the data. Please enter UTC time. Format for the Start Time would be `MM/DD/YYYY hh:mm:ss`.

5. Click on the `Add` green button on the bottom right of the pop up box.
6. Please check for any errors and resolve them before using the search app to check for the pulled-in data.

## Example(s)

### Input type: Active Session 

<img src="appserver/static/img/Input%20-%20Active%20Sessions.png"  width="600" height="450">

### Input type: Historical Meetings

<img src="appserver/static/img/Input%20-%20Historical%20Meetings.png"  width="600" height="450">



## Credits & Acknowledgements (optional)
> Built by Splunk's FDSE Team (#team-fdse). 
