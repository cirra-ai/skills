@isTest
public class DBM25ControllerTest {

    @isTest
    public static void dbm25Test() {
        String namespace = DBM25Controller.getPackageNamespace();
        List<String> picklistValues = DBM25Controller.getPicklistValues('Opportunity', 'StageName');
        List<Folder> folders = DBM25Controller.getReportFolders();
        List<DBM_Report__c> records = DBM25Controller.getReportDetailRecords();

        // String demoString = '{"maxNumGroupings":2,"numGroupings":2,"metricType":"percent-fixed","metricName":"custom","groupings":[{"dataSource":"custom","entries":[{"id":"a04bm000000HVdhAAG","value":"A"},{"id":"a04bm000000HVdiAAG","value":"B"},{"id":"a04bm000000HVdjAAG","value":"C"},{"id":"a04bm000000HVdkAAG","value":"D"},{"id":"a04bm000000HVdlAAG","value":"E"}],"presetEntries":[],"id":"a03bm0000029r2LAAQ","name":"Test","classString":"slds-col slds-p-horizontal_none slds-size_1-of-2","dataSourceIs":{"custom":true},"groupingNumber":1,"enumerateClass":"neutral","inputLabel":"Enter Name for Grouping #1","isDisabled":false},{"dataSource":"months","entries":[{"id":"a04bm000000HVdmAAG","value":"January"},{"id":"a04bm000000HVdnAAG","value":"February"},{"id":"a04bm000000HVdoAAG","value":"March"},{"id":"a04bm000000HVdpAAG","value":"April"},{"id":"a04bm000000HVdqAAG","value":"May"},{"id":"a04bm000000HVdrAAG","value":"June"},{"id":"a04bm000000HVdsAAG","value":"July"},{"id":"a04bm000000HVdtAAG","value":"August"},{"id":"a04bm000000HVduAAG","value":"September"},{"id":"a04bm000000HVdvAAG","value":"October"},{"id":"a04bm000000HVdwAAG","value":"November"},{"id":"a04bm000000HVdxAAG","value":"December"}],"presetEntries":[],"id":"a03bm0000029r2MAAQ","name":"Month","classString":"slds-col slds-p-horizontal_none slds-size_1-of-2","dataSourceIs":{"months":true},"groupingNumber":2,"enumerateClass":"neutral","inputLabel":"Enter Name for Grouping #2","isDisabled":false}],"data":[[62,55,41,20,62,54,10,59,8,32,21,66],[32,7,16,12,15,94,84,66,34,83,42,42],[1,46,28,94,86,27,98,70,13,13,51,90],[15,89,17,47,26,35,84,76,43,91,95,0],[91,40,11,47,42,58,98,70,70,30,14,76]],"chartType":"stackvbar","id":"a02bm000001PI7dAAG","reportName":"Change Over Time","metricIsCustom":true,"customMetricName":"Percent Change","folderDeveloperName":"TestDBMFolder","reportId":"00Obm000003WqMjEAK","metricLabel":"Percent Change"}';
        String demoString = '{"maxNumGroupings":2,"numGroupings":1,"metricType":"number","metricName":"recordCount","groupings":[{"dataSource":"custom","entries":[{"id":"a01O300000In86vIAB","value":"Test Grouping Entry 1"},{"id":"a01O300000In86wIAB","value":"Test Grouping Entry 2"},{"id":"a01O300000In86xIAB","value":"Test Grouping Entry 3"}],"presetEntries":[],"id":"a02O30000070whVIAQ","name":"This is a test grouping","classString":"slds-col slds-p-horizontal_none slds-size_1-of-1","dataSourceIs":{"custom":true},"groupingNumber":1,"enumerateClass":"neutral","inputLabel":"Enter Name for Grouping #1","isDisabled":false},{"dataSource":"custom","entries":[],"presetEntries":[],"classString":"slds-col slds-p-horizontal_none slds-hide","dataSourceIs":{"custom":true},"groupingNumber":2,"enumerateClass":"neutral","inputLabel":"Enter Name for Grouping #2","isDisabled":true}],"data":[[36],[94],[86]],"chartType":"vbar","isClone":true,"id":null,"reportName":"Copy of This is a test report","folderDeveloperName":"DashboardMagicReports","reportId":null,"metricLabel":"Record Count"}';
        Map<String, Object> saveResult = DBM25Controller.saveReportDetails(demoString);
        System.assertEquals(saveResult.get('isSuccess'), true);

        DBM25Controller.createReport((String)saveResult.get('reportId'));

        DBM25Controller.sendFeedback('Subject', 'Body');

        // (String searchTerm, String objectName, String fieldsToSearch, String fieldsToReturn, Integer numRecordsToReturn, String whereClause, String orderByClause) {
        List<SObject> searchAccounts = FscLookupController.search('Omega', 'Account', 'Name', 'Id', 5, null, 'CreatedDate ASC');
        List<SObject> recentAccounts = FscLookupController.getRecentlyViewed('Account', 'Id', 5, null);
        String accountNameField = FscLookupController.getNameField('Account');
        System.assertEquals(accountNameField, 'Name');
    }
}