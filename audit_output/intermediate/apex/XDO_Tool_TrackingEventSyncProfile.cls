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
 * @date 21/1/2024
 *
 * TODO:
 */

 public class XDO_Tool_TrackingEventSyncProfile extends XDO_Tool_QueueableBase implements Database.AllowsCallouts //NOPMD
 {
     public static final String SYNC_ERROR_ACTION = 'Scheduled profile sync execution';
 
     private XDO_Tool_TrackingEventService service;
 
     /**
      * Constructors
      */
     public XDO_Tool_TrackingEventSyncProfile() {
     }
 
     public XDO_Tool_TrackingEventSyncProfile(XDO_Tool_TrackingEventService service) {
         super();
         this.setService(service);
     }
 
     public override XDO_Tool_QueueableBase setService(XDO_Tool_IQueueableService service) {
         this.service = (XDO_Tool_TrackingEventService)service;
 
         return this;
     }
 
     public override void execute(System.QueueableContext context) {
         try {
             List<XDO_Tool_Tracking_Event__c> events = [
                     SELECT Error__c,
                             User__r.FirstName,
                             User__r.LastName,
                             Email__c,
                             CreatedDate,
                             Stage__c
                     FROM XDO_Tool_Tracking_Event__c
                     WHERE Stage__c = :this.config.Entry_Stage__c
                     AND Error__c = ''
                     ORDER BY CreatedDate ASC
                     LIMIT :this.batchSize
             ];
 
             service.transformProfiles(events)
                     .loadProfiles()
                     .finalize(events, this.config.Exit_Stage__c);

         } catch (Exception e) {
             new XDO_Tool_TrackingEventProduct.Error()
                     .setMessage(String.format('{0} : {1}', new List<String>{
                             XDO_Tool_Utilities.getClassName(this), e.getMessage()
                     }))
                     .setAction(SYNC_ERROR_ACTION)
                     .setAssetIdentifier(System.Label.xDO_Tool_Tracking_Event_Version)
                     .publish();
         } finally {
             this.reQueueJob();
         }
     }
 
     protected override Boolean shouldChainQueueable() {
         return super.shouldChainQueueable() &&
                 [
                         SELECT COUNT()
                         FROM XDO_Tool_Tracking_Event__c
                         WHERE Stage__c = :this.config.Entry_Stage__c
                         AND Error__c = ''
                 ] > 0;
     }
 }