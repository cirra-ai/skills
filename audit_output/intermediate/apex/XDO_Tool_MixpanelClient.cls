/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */


/**
 * @author Paul Lucas
 * @company       Salesforce
 *
 * @date 1/1/2024
 *
 *
 */

 public without sharing class XDO_Tool_MixpanelClient extends XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient  //NOPMD
 {
     public static final String PROJECT_ID = 'projectId';
     public static final String PROJECT_TOKEN = 'projectToken';
     public static final String EVENT_TRANSFORMATION_MAPPING = 'xDO_Tool_TrackingEventToMixpanel';
     public static final String PROFILE_TRANSFORMATION_MAPPING = 'xDO_Tool_TrackingEventToMixpanelProfile';
     public static final String SYNC_ERROR_MESSAGE = 'Error importing tracking events';
     public static final String SYNC_ERROR_ACTION = 'Import tracking events';
 
     public enum DATAWEAVE_INPUT {
         payload, context
     }
 
     public enum SERVICE_PARAMETER {
         strict, verbose, project_id
     }
 
     public enum MIXPANEL_ERROR {
         failed_validation
     }
 
     public static Map<MIXPANEL_ERROR, String> MIXPANEL_ERROR_MESSAGE = new Map<MIXPANEL_ERROR, String>{
             MIXPANEL_ERROR.failed_validation => 'some data points in the request failed validation'
     };
 
     public Integer projectId;
     public String projectToken;
     public Set<Object> profiles;
     public List<Object> body;
 
     public MixpanelResponse response {
         get;
         private set;
     }
 
     public String responseString {
         get {
             return (this.response != null) ? JSON.serialize(this.response) : this.responseString;
         }
         set {
             if (this.response != null) {
                 this.responseString = value;
             }
         }
     }
 
     /**
      * Constructors
      */
     public XDO_Tool_MixpanelClient() {
     }
 
     public XDO_Tool_MixpanelClient(Integer projectId, String projectToken, String namedCredential) {
         super(namedCredential);
 
         this.initialize(new Map<String, String>{
                 PROJECT_ID => String.valueOf(projectId),
                 PROJECT_TOKEN => projectToken
         });
     }
 
     /**
      * initialize: Client initialization
      *
      * @param parameters
      *
      * @return
      */
     public override XDO_Tool_ApiService.Client initialize(Map<String, String> parameters) {
         this.profiles = new Set<Object>();
         this.body = new List<Object>();
         this.response = new MixpanelResponse();
         this.projectId = Integer.valueOf(parameters.get(PROJECT_ID).trim());
         this.projectToken = parameters.get(PROJECT_TOKEN).trim();
 
         return this;
     }
 
     /**
      * handleError: Handle error response
      *
      * @param response
      */
     protected override void handleError(XDO_Tool_ApiService.ApiServiceResponse response) {
         try {
             this.response = (MixpanelResponse) JSON.deserialize(response.body, MixpanelResponse.class);
 
             if (this.response.error == MIXPANEL_ERROR_MESSAGE.get(MIXPANEL_ERROR.failed_validation)) {
                 response.ignoreError(true);
             }
         } catch (JSONException e) {
             system.debug('>>>>> handleError: Error deserializing Mixpanel response.');
         }
     }
 
     /**
      * handleResponse: Handle callout response
      *
      * @param response
      */
     protected override void handleResponse(Object response) {
         if (response instanceof MixpanelResponse) {
             this.response = (MixpanelResponse) response;
         } else if (response instanceof String) {
             this.responseString = String.valueOf(response);
         }
     }
 
     /**
      * addRequestItem : Add an item to the request body
      *
      * @param item
      */
     private void addRequestItem(Object item) {
         if (item != null) {
             this.body.add(item);
         }
     }
 
     /**
      * resetProfiles : Reset profile list
      */
     public void resetProfiles() {
         this.profiles.clear();
     }
 
     /**
      * addProfile : Add a Mixpanel profile to load
      *
      * @param profile
      */
     public void addProfile(Object profile) {
         this.profiles.add(profile);
     }
 
     /**
      * disableValidation : Skip validation of events. Validation is required for error tracking - https://developer.mixpanel.com/reference/import-events
      *
      * @return
      */
     public XDO_Tool_MixpanelClient disableValidation() {
         setQuery(new XDO_Tool_ApiService.Param(XDO_Tool_MixpanelClient.SERVICE_PARAMETER.strict.name(), '0'));
 
         return this;
     }
 
     /**
      * transformEvents: Transform to Mixpanel events
      *
      * @param trackingEvents
      *
      * @return
      */
     public override XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient transformEvents(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
         String payload;
         DataWeave.Script script = DataWeave.Script.createScript(EVENT_TRANSFORMATION_MAPPING);
 
         for (XDO_Tool_Tracking_Event__c event : trackingEvents) {
             payload = script.execute(new Map<String, Object>{
                     DATAWEAVE_INPUT.payload.name() => event.Payload__c,
                     DATAWEAVE_INPUT.context.name() => new XDO_Tool_TrackingEvent.Context(event).serialize()
             })?.getValueAsString();
 
             if (String.isNotBlank(payload)) {
                 addRequestItem(JSON.deserializeUntyped(payload));
             }
         }
 
         return (XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient)this;
     }
 
     /**
      * processEvents: Import Mixpanel events - https://developer.mixpanel.com/reference/import-events
      *
      * @return
      */
     public override XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient importEvents() {
 //        setAuthentication(XDO_Tool_ApiService.AUTH_TYPE.Header, XDO_Tool_ApiService.AUTHENTICATION_SCHEME.get(XDO_Tool_ApiService.AUTHENTICATION_SCHEME_TYPE.basic), this.serviceAccount);
         setQuery(new XDO_Tool_ApiService.Param(XDO_Tool_MixpanelClient.SERVICE_PARAMETER.strict.name(), '1'));
         setQuery(new XDO_Tool_ApiService.Param(XDO_Tool_MixpanelClient.SERVICE_PARAMETER.project_id.name(), String.valueOf(this.projectId)));
 
         if (!this.body.isEmpty()) {
             invoke(XDO_Tool_ApiService.HTTP_METHOD.POST,
                     '/import',
                     this.body,
                     MixpanelResponse.class
             );
         }
 
         return (XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient)this;
     }
 
     /**
      * transformProfiles: Transform to Mixpanel profiles
      *
      * @param trackingEvents
      *
      * @return
      */
     public override XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient transformProfiles(List<XDO_Tool_Tracking_Event__c> trackingEvents) {
         String payload;
         DataWeave.Script script = DataWeave.Script.createScript(PROFILE_TRANSFORMATION_MAPPING);
 
         resetProfiles();
 
         for (XDO_Tool_Tracking_Event__c event : trackingEvents) {
             if (String.isNotBlank(event.Email__c)) {
                 addProfile(new UserProfile(event));
             }
         }
 
         payload = script.execute(new Map<String, Object>{
                 DATAWEAVE_INPUT.payload.name() => JSON.serialize(this.profiles),
                 DATAWEAVE_INPUT.context.name() => JSON.serialize(new Map<String, String>{
                         PROJECT_TOKEN => this.projectToken
                 })
         })?.getValueAsString();
 
         if (String.isNotBlank(payload)) {
             this.body = (List<Object>) JSON.deserializeUntyped(payload);
         }
 
         return (XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient)this;
     }
 
     /**
      * setProfiles: Create or update Mixpanel profiles : https://developer.mixpanel.com/reference/profile-set
      *
      * @return
      */
     public override XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient setProfiles() {
         setQuery(new XDO_Tool_ApiService.Param(XDO_Tool_MixpanelClient.SERVICE_PARAMETER.verbose.name(), '1'));
 
         if (!this.body.isEmpty()) {
             invoke(XDO_Tool_ApiService.HTTP_METHOD.POST,
                     '/engage#profile-set',
                     this.body,
                     MixpanelResponse.class
             );
         }
 
         return (XDO_Tool_TrackingEventService.XDO_Tool_TrackingEventClient)this;
     }
 
     /**
      * processResults: Save errors back to XDO_Tool_Tracking_Event__c
      *
      * @param events
      *
      * @return
      */
     public override List<XDO_Tool_Tracking_Event__c> processResults(List<XDO_Tool_Tracking_Event__c> events) {
         if (this.response?.hasFailedRecords()) {
             for (MixpanelFailedRecords record : this.response.failed_records) {
                 events[record.index].Error__c = String.format('{0} : {1}', new List<String>{
                         XDO_Tool_Utilities.getClassName(this), record.message
                 });
             }
 
             update events;
 
             new XDO_Tool_TrackingEventProduct.Error()
                     .setMessage(String.format('{0} : {1}', new List<String>{
                             XDO_Tool_Utilities.getClassName(this), SYNC_ERROR_MESSAGE
                     }))
                     .setAction(SYNC_ERROR_ACTION)
                     .setAssetIdentifier(System.Label.xDO_Tool_Tracking_Event_Version)
                     .publish();
         }
 
         return events;
     }
 
     /**
      * Canonical User Profile
      */
     public class UserProfile {
         String firstName;
         String lastName;
         String email;
 
         public UserProfile(XDO_Tool_Tracking_Event__c event) {
             this(event.User__r?.FirstName, event.User__r?.LastName, event?.Email__c);
         }
 
         public UserProfile(String firstName, String lastName, String Email) {
             this.firstName = firstName;
             this.lastName = lastName;
             this.email = Email;
         }
     }
 
     /**
      * Mixpanel response
      */
     public class MixpanelResponse {
         public Integer code {
             get {
                 if (this.code == null) {
                     this.code = 200;
                 }
                 return this.code;
             }
             set;
         }
 
         String error;
         List<MixpanelFailedRecords> failed_records;
         Integer num_records_imported;
         String status;
 
         public MixpanelResponse() {
             this.failed_records = new List<XDO_Tool_MixpanelClient.MixpanelFailedRecords>();
         }
 
         public Boolean hasFailedRecords() {
             return this.failed_records != null &&
                     this.failed_records.size() > 0;
         }
     }
 
     public class MixpanelFailedRecords {
         Integer index;
         String insert_id;
         String field;
         String message;
     }
 }