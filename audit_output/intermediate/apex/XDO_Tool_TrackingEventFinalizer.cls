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
 * @date 6/2/2024
 *
 * TODO:
 */

public with sharing class XDO_Tool_TrackingEventFinalizer extends XDO_Tool_TrackingEventProcessor //NOPMD
{
    private static final String EMAIL_DOMAIN_SALESFORCE = '%@salesforce.com';
    private static final String SYSTEM_USER_ALIAS = 'autocase';
    private static final String PRIMARY_ADMIN_EXTERNAL_ID = 'User.001';
    private static final String PROFILE_TYPE_ADMIN = 'Admin';
    private static final String PROFILE_NAME_SYSTEM_ADMINISTRATOR = 'System Administrator';
    private static final String DML_FAILED_TO_INSERT_EVENTS_MESSAGE = '>>>>> {0}: Failed to insert events';

    public XDO_Tool_TrackingEventFinalizer() {
        this(null);
    }

    public XDO_Tool_TrackingEventFinalizer(XDO_Tool_TrackingEventProcessor next) {
        super(next);
    }

    public override void process(List<XDO_Tool_Platform_Tracking_Event__e> trackingEvents) {
        Database.SaveResult[] results;
        List<XDO_Tool_Tracking_Event__c> events = new List<XDO_Tool_Tracking_Event__c>();

        // List<Profile> adminProfiles = [
        //         SELECT Id
        //         FROM Profile
        //         WHERE Name = :PROFILE_NAME_SYSTEM_ADMINISTRATOR
        // ];

        Set<Id> internalUsers = new Map<Id, SObject>([
                SELECT Id
                FROM User
                WHERE Email LIKE :EMAIL_DOMAIN_SALESFORCE
                AND IsActive = TRUE
                AND LastLoginDate != NULL
                AND Alias != :SYSTEM_USER_ALIAS
                // AND (External_ID__c = :PRIMARY_ADMIN_EXTERNAL_ID
                // OR ProfileId IN :adminProfiles)
                ORDER BY LastLoginDate DESC
        ]).keySet();

        for (XDO_Tool_Platform_Tracking_Event__e event : trackingEvents) {
            events.add(
                    new XDO_Tool_Tracking_Event__c(
                            Action__c = event.Action__c,
                            Asset_Identifier__c = event.Asset_Identifier__c,
                            Event_Date__c = event.Event_Date__c != null ? event.Event_Date__c : System.now(),
                            Event__c = event.Event__c,
                            Once__c = event.Once__c,
                            Payload__c = event.Payload__c,
                            Type__c = event.Type__c,
                            Unique_Id__c = String.isBlank(event.Unique_Id__c) ? UUID.randomUUID().toString() : event.Unique_Id__c.trim(),
                            User__c = String.isBlank(event.User_Id__c) ? internalUsers?.iterator().next() : event.User_Id__c
                    ));
        }

        if (!trackingEvents.isEmpty()) {
            try {
                results = Database.insert(events, false);
            } catch (DmlException e) {
                System.debug(String.format(DML_FAILED_TO_INSERT_EVENTS_MESSAGE, new List<String>{
                        XDO_Tool_Utilities.getClassName(this)
                }));

                System.debug(e.getMessage());

                for (Integer i = 0; i < results.size(); i++) {
                    if (!results[i].isSuccess()) {
                        System.debug(results[i].getErrors());
                    }
                }

                // TODO: Test if this block is reached when allOrNothing is false
                //  Stage error as trackingevent
//                Integer numErrors = e.getNumDml();
//                String errorMessage = 'There were ' + numErrors + ': ';
//                for(Integer errorIdx = 0; errorIdx < numErrors; errorIdx++) {
//                    errorMessage += 'Field Names = ' + de.getDmlFieldNames(errorIdx);
//                    errorMessage += 'Message = ' + de.getDmlMessage(errorIdx);
//                    errorMessage += ' , ';
//                }
            }
        }

        super.process(trackingEvents);
    }
}