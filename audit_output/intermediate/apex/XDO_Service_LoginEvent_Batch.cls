global class XDO_Service_LoginEvent_Batch implements Database.Batchable<sObject>, Database.AllowsCallouts, Database.Stateful {
    global Datetime export_start;
    global Datetime export_end;

    private static final String LOGIN_SUCCESS = 'Success';
    private static final String ACTION_NAME = 'Login via ';
    private final Set<String> TRACKED_APPLICATIONS = new Set<String>();

    private final static Set<String> LOGIN_TYPE = new Set<String>{
            'Application', 'Remote Access 2.0'
    };

    private final Organization org = [
            SELECT Name
            FROM Organization
            LIMIT 1
    ];

    private final QLabs__mdt orgMetadata = [
            SELECT Id,
                    DeveloperName,
                    Identifier__c,
                    Label,
                    MasterLabel,
                    Org_Type__c,
                    QualifiedApiName
            FROM QLabs__mdt
            WHERE DeveloperName = 'Org_Identifier'
            LIMIT 1
    ];

    global XDO_Service_LoginEvent_Batch(Datetime startPeriod, Datetime endPeriod) {
        export_start = startPeriod;
        export_end = endPeriod;
    }

    global Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
                SELECT Id,
                        UserId,
                        LoginTime,
                        Application,
                        Platform,
                        Status
                FROM LoginHistory
                WHERE LoginType IN :LOGIN_TYPE
                AND (
                        LoginTime >= :export_start
                        AND LoginTime < :export_end
                )
                ORDER BY UserId DESC
        ]);
    }

    global void execute(Database.BatchableContext bc, List<LoginHistory> logins) {
        String className = XDO_Tool_Utilities.getClassName(this);
        List<XDO_Tool_Platform_Tracking_Event__e> loginEvents = new List<XDO_Tool_Platform_Tracking_Event__e>();

        // Not required for GDO's
//        Set<Id> userIds = new Set<Id>();
//        Map<Id, User> usersById = new Map<Id, User>();
//
//        for (LoginHistory login : logins) {
//            userIds.add(login.UserId);
//        }
//
//        usersById = new Map<Id, User>([
//                SELECT Profile.Name
//                FROM User
//                WHERE Id IN :userIds
//        ]);
//
        try {
            if (TRACKED_APPLICATIONS == null || TRACKED_APPLICATIONS.size() == 0) {
                for (xDO_Service_TrackedLoginApplication__mdt applicationType : [
                        SELECT MasterLabel
                        FROM xDO_Service_TrackedLoginApplication__mdt
                ]) {
                    TRACKED_APPLICATIONS.add(applicationType.MasterLabel);
                }
            }

            for (LoginHistory login : logins) {
                if (login.Status == LOGIN_SUCCESS && TRACKED_APPLICATIONS.contains(login.Application)) {

                    loginEvents.add(new XDO_Tool_TrackingEventReporting.Conversion()
                            .setMinutesSaved(1)
                            // .setAction(ACTION_NAME + login.Application)
                            .setAction('Shared Demo Org Login')
                            .addProperty('application', login.Application)
                            .addProperty('org_identifier', orgMetadata.Identifier__c)
                            .addProperty('org_name', org.Name)
                            // .setAssetIdentifier('testloginhistory)
                            .setAssetIdentifier(className)
                            .setEventDate(login.LoginTime)
                            .setSource(org.Name)
                            .setUniqueId(login.Id)
                            .setUserId(login.UserId)
                            .getEvent());
                }
            }

            EventBus.publish(loginEvents);
        } catch (Exception e) {
            // TODO: Add logging module
            System.debug('>>>>> ' + className + ' execute exception: ');
            System.debug(e.getMessage());
            System.debug(logins);
        }
    }

    global void finish(Database.BatchableContext bc) {
        String className = XDO_Tool_Utilities.getClassName(this);

        System.debug('>>>>> ' + className + ' batch finished');
    }
}