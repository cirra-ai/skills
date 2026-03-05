public without sharing class SDO_Experience_RecordSnapshotCtrl {
    @AuraEnabled(cacheable = true)
    public static Map < String, Integer > getTaskList() {

        Map < String, Integer > taskCounts = new Map < String, Integer > ();

        // Query for the count of upcomingCount tasks
        Integer upcomingCount = [SELECT COUNT() FROM Task WHERE OwnerId =: UserInfo.getUserId() AND Status != 'Completed'
            AND ActivityDate > TODAY
        ];
        taskCounts.put('upcomingCount', upcomingCount);

        // Query for the count of open tasks (excluding overdue tasks)
        Integer overdueCount = [SELECT COUNT() FROM Task WHERE OwnerId =: UserInfo.getUserId() AND Status != 'Completed'
            AND ActivityDate < TODAY
        ];
        taskCounts.put('overdueCount', overdueCount);

        return taskCounts;
    }

    @AuraEnabled(cacheable = true)
    public static Map < String, Integer > getCaseList() {
        System.debug('getCaseList running...');
        Map < String, Integer > caseCounts = new Map < String, Integer > ();

        User theUser = [SELECT ContactId, AccountId FROM User WHERE Id =: UserInfo.getUserId()];
        System.debug('the contact is: ' + theUser.ContactId);

        // Query for Open cases where the current user is the owner or contact on the case and the status <> closed
        Integer openCount = [SELECT COUNT() FROM Case WHERE(OwnerId =: UserInfo.getUserId() OR ContactId =: theUser.ContactId) AND Status != 'Closed'];
        caseCounts.put('openCount', openCount);

        // Need Review cases where the current user is the owner or contact on the case and the status (waiting on customer).
        Integer reviewCount = [SELECT COUNT() FROM Case WHERE(OwnerId =: UserInfo.getUserId() OR ContactId =: theUser.ContactId) AND Status != 'Waiting on Customer'];
        caseCounts.put('reviewCount', reviewCount);

        return caseCounts;
    }

    @AuraEnabled(cacheable = true)
    public static Map < String, Integer > getAssetList() {

        Map < String, Integer > assetCounts = new Map < String, Integer > ();

        User theUser = [SELECT ContactId, AccountId FROM User WHERE Id =: UserInfo.getUserId()];

        // Query for Assets owned by my company
        Integer purchasesCount = [SELECT COUNT() FROM Asset WHERE AccountId =: theUser.AccountId];
        assetCounts.put('purchasesCount', purchasesCount);

        // Query for the count of open tasks (excluding overdue tasks)
        Integer registeredCount = [SELECT COUNT() FROM Asset WHERE AccountId =: theUser.AccountId AND Entitlement_Status__c != null];
        assetCounts.put('registeredCount', registeredCount);

        return assetCounts;
    }

    @AuraEnabled(cacheable = true)
    public static Map < String, Integer > getLeadList() {

        Map < String, Integer > leadCounts = new Map < String, Integer > ();

        // Leads with status of New, Draft, Pending, Working, Submitted, Approved, or Qualified and where the current user is the lead owner.
        Integer leadCount = [SELECT COUNT() FROM Lead WHERE OwnerId =: UserInfo.getUserId() AND Status IN('New', 'Draft', 'Pending', 'Working', 'Submitted', 'Approved', 'Qualified')];
        leadCounts.put('leadCount', leadCount);

        // Leads with a status of New, Draft, Pending, Working, Submitted, Approved, or Qualified and where the current user is the lead owner and where Rating = Hot).
        Integer hotCount = [SELECT COUNT() FROM Lead WHERE OwnerId =: UserInfo.getUserId() AND Status IN('New', 'Draft', 'Pending', 'Working', 'Submitted', 'Approved', 'Qualified')
            AND Rating = 'Hot'
        ];
        leadCounts.put('hotCount', hotCount);

        return leadCounts;
    }

    @AuraEnabled(cacheable = true)
    public static Map < String, Integer > getOppList() {

        Map < String, Integer > oppCounts = new Map < String, Integer > ();

        Date thirtyDaysAgo = Date.today().addDays(-30);

        // Opportunities with Stage <> Closed Won or Closed Lost where current user is the opportunity owner.
        Integer oppCount = [SELECT COUNT() FROM Opportunity WHERE OwnerId =: UserInfo.getUserId() AND StageName NOT IN('Closed Won', 'Closed Lost')];
        oppCounts.put('oppCount', oppCount);

        // Opportunities with Stage <> Closed Won or Closed Lost where current user is the opportunity owner and the created was within the last 30 days.
        Integer thisMonthCount = [SELECT COUNT() FROM Opportunity WHERE OwnerId =: UserInfo.getUserId() AND StageName NOT IN('Closed Won', 'Closed Lost') AND CreatedDate >=: thirtyDaysAgo];
        oppCounts.put('thisMonthCount', thisMonthCount);

        return oppCounts;
    }
}