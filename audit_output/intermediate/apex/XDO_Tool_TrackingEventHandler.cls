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
 * @date 25/11/2023
 *
 * TODO:
 */

 public without sharing class XDO_Tool_TrackingEventHandler extends TriggerHandler //NOPMD
 {
     private List<XDO_Tool_Platform_Tracking_Event__e> trackingEventsOldList;
     private Map<Id, XDO_Tool_Platform_Tracking_Event__e> trackingEventsOldMap;
     private List<XDO_Tool_Platform_Tracking_Event__e> trackingEventsNewList;
     private Map<Id, XDO_Tool_Platform_Tracking_Event__e> trackingEventsNewMap;
 
     private Set<Id> userIds = new Set<Id>();
     private Map<Id, User> usersById = new Map<Id, User>();
 
     public XDO_Tool_TrackingEventHandler() {
         this.trackingEventsOldList = Trigger.old != null ? (List<XDO_Tool_Platform_Tracking_Event__e>) Trigger.old.clone() : new List<XDO_Tool_Platform_Tracking_Event__e>();
         this.trackingEventsOldMap = Trigger.oldMap != null ? (Map<Id, XDO_Tool_Platform_Tracking_Event__e>) Trigger.oldMap.clone() : new Map<Id, XDO_Tool_Platform_Tracking_Event__e>();
         this.trackingEventsNewList = Trigger.new != null ? (List<XDO_Tool_Platform_Tracking_Event__e>) Trigger.new.clone() : new List<XDO_Tool_Platform_Tracking_Event__e>();
         this.trackingEventsNewMap = Trigger.newMap != null ? (Map<Id, XDO_Tool_Platform_Tracking_Event__e>) Trigger.newMap.clone() : new Map<Id, XDO_Tool_Platform_Tracking_Event__e>();
     }
 
     public override void afterInsert() {
 //        lookupContactsByUser(); // TODO: Determine if we want to capture the acting community contact user
 
         XDO_Tool_TrackingEventProcessor.getProcessors()
                 .process(this.trackingEventsNewList);
 
         scheduleJobs();
     }
 
//     public void lookupContactsByUser() {
//         for (XDO_Tool_Platform_Tracking_Event__e e : this.trackingEventsNewList) {
//             if (e.User_Id__c != null) {
//                 this.userIds.add(e.User_Id__c);
//             }
//         }
//
//         this.usersById = new Map<Id, User>([
//                 SELECT AccountId,
//                         ContactId,
//                         FirstName,
//                         LastName,
//                         Email,
//                         CompanyName,
//                         Country
//                 FROM User
//                 WHERE Id IN :userIds
//         ]);
//     }
 
     /**
      * scheduleJobs: Call job schedulers
      */
     private void scheduleJobs() {
         if (!this.trackingEventsNewList.isEmpty()) {
            //  if (Math.mod(Integer.valueOf(this.trackingEventsNewList[0].ReplayId), 2) == 0) {
                 new XDO_Tool_TrackingEventJobScheduler().queue();
            //  }
         }
     }
 }