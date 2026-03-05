// David Fromstein, Dec 2020
// david.fromstein@salesforce.com
// Requires and is heavily based off MetadataService.cls

global class SDO_Analytics_ReportFakerController {

    public class MetadataServiceExamplesException extends Exception { }

    public static String SOAP_M_URI = 'http://soap.sforce.com/2006/04/metadata';
    public static DescribeSObjectResult fakeObjRes = Fake_Report_Data_Object__c.getSObjectType().getDescribe();
    private static String folderName = 'DashboardMagicReports';
    public static Integer apiNameMaxLength = 40;

    // Controller for the VF page
    public PageReference vfController() {
        String reportName = getVFParam('group');//ApexPages.currentPage().getParameters().get('group').unescapeHtml4();
        String primaryGrouping = getVFParam('primaryGrouping');//ApexPages.currentPage().getParameters().get('primaryGrouping').unescapeHtml4();
        String secondaryGrouping = getVFParam('secondaryGrouping');//ApexPages.currentPage().getParameters().get('secondaryGrouping').unescapeHtml4();
        String metricName = getVFParam('metricName');//ApexPages.currentPage().getParameters().get('metricName').unescapeHtml4();
        String metricType = getVFParam('metricType');//ApexPages.currentPage().getParameters().get('metricType').unescapeHtml4();
        System.debug('in report controller constructor: '+ folderName +', '+ reportName +', '+ primaryGrouping +', '+ secondaryGrouping +', '+ metricName+', '+ metricType);
        MetadataService.SaveResult reportResult = createReport(folderName, reportName, primaryGrouping, secondaryGrouping, metricName, metricType);
        System.debug('reportResult = '+ reportResult);
        if (reportResult.success) {
            String reportDeveloperName = reportResult.fullName.split('/')[1];
            Id reportId = [SELECT Id FROM Report WHERE DeveloperName = :reportDeveloperName].Id;
            PageReference loadReport = new PageReference('/' + reportId);
            //PageReference loadReport = new PageReference('javascript:window.close()');
            
            loadReport.setRedirect(true);
            return loadReport;
        }
        return null;
    }

    private String getVFParam(String paramName) {
        String value = ApexPages.currentPage().getParameters().get(paramName);
        System.debug('paramName = '+ paramName+', value = '+ value);
        if (String.isBlank(value))
            return null;
        return value.unescapeHtml4();
    }


    public static Map<String, String> fakeObjectFields {
        get {
            Map<String, String> returnMap = new Map<String, String>();
            returnMap.put('id', 'Id');
            returnMap.put('group', 'Group__c');
            returnMap.put('primaryGrouping', 'Label__c');
            returnMap.put('secondaryGrouping', 'Secondary_Grouping__c');
            returnMap.put('value', 'Value__c');
            return returnMap;
        }        
    }

    global class SaveFakesRequest {
        @AuraEnabled global String reportName;
        @AuraEnabled global String primaryGrouping;
        @AuraEnabled global String secondaryGrouping;
        @AuraEnabled global String fakeDataString;

        //global SaveFakesRequest() {            
        //}    
    }

    public class SaveFakesResult {

    }

    @AuraEnabled
    public static String saveFakeData(String fakeDataString) {
        System.debug(JSON.deserializeUntyped(fakeDataString));
        List<Object> fakeData = (List<Object>) JSON.deserializeUntyped(fakeDataString);
        System.debug(fakeData);
        List<Fake_Report_Data_Object__c> fakes = new List<Fake_Report_Data_Object__c>();
        Set<String> groupSet = new Set<String>();
        for (Object fake : fakeData) {
            Map<String, Object> fakeRecord = (Map<String, Object>) JSON.deserializeUntyped(JSON.serialize(fake));
            Fake_Report_Data_Object__c newFake = new Fake_Report_Data_Object__c();
            newFake.Group__c = (String) fakeRecord.get('group');
            groupSet.add(newFake.Group__c);
            newFake.Label__c = (String) fakeRecord.get('label');
            newFake.Secondary_Grouping__c = (String) fakeRecord.get('secondary');
            newFake.Value__c = Double.valueOf(fakeRecord.get('value'));
            System.debug(newFake);
            fakes.add(newFake);
        }
        if (fakes.isEmpty()) {
            return 'Why have you done this';
        }
        // Delete any pre-existing fake data under the same group name(s)
        delete [SELECT Id FROM Fake_Report_Data_Object__c WHERE Group__c IN :groupSet];

        // Insert new fake data
        insert fakes;

        return JSON.serialize(fakes);
    }

    @AuraEnabled(cacheable=true)
    public static List<Fake_Report_Data_Object__c> getExistingFakeData() {
        return [SELECT Id, Group__c, Label__c, Secondary_Grouping__c, Value__c FROM Fake_Report_Data_Object__c];
    }

    @AuraEnabled
    public static List<Fake_Report_Data_Object__c> getExistingGroupMembers(String reportName) {
        List<Fake_Report_Data_Object__c> existingFakes = [SELECT Id, Group__c, Label__c, Secondary_Grouping__c, Value__c FROM Fake_Report_Data_Object__c WHERE Group__c =: reportName];
        return existingFakes;        
    }

    @AuraEnabled(cacheable=true)
    public static String getBaseReportId() {
        List<Report> r = [SELECT Id FROM Report WHERE Name LIKE '*Fake* Data Report%'];
        if (r.size() != 1)
            return null;
        return r[0].Id;
    }

    //@AuraEnabled
    public static MetadataService.SaveResult createReport(String folderName, String reportName, String primaryGrouping, String secondaryGrouping, String metricName, String metricType) {
        System.debug('in createReport: '+ folderName +', '+ reportName +', '+ primaryGrouping +', '+ secondaryGrouping +', '+ metricName+', '+ metricType);
        MetadataService.MetadataPort service = createService();
        MetadataService.Report newReport = new MetadataService.Report();

        /* Do some metadata processing */
        String[] columnFieldNames = new String[]{};// (we don't actually need these columns in the report) {'Value__c', 'Amount__c', 'Percent__c', 'Group__c', 'Label__c', 'Secondary_Grouping__c'};
        System.debug('columnFieldNames = '+ columnFieldNames);
        MetadataService.ReportColumn[] columns = new List<MetadataService.ReportColumn>();
        MetadataService.ReportBucketField[] buckets = new List<MetadataService.ReportBucketField>();
        MetadataService.ReportGrouping[] groupings = new List<MetadataService.ReportGrouping>();
        MetadataService.ReportAggregate[] aggregates = new List<MetadataService.ReportAggregate>();
        MetadataService.ReportFilter filter = new MetadataService.ReportFilter();
        MetadataService.ReportChart chart = null;//getMetadataChart(fakeObjRes.getName() + '.' + columnFieldNames[0]);
        for (String fieldName : columnFieldNames) {
            //fieldName = fieldName.replace('dflabs__','');
            String fullFieldName = fakeObjRes.getName() +'.'+ fieldName;
            String fieldType = fakeObjRes.fields.getMap().get(fieldName).getDescribe().getType().name().toLowerCase();
            boolean isNumber = fieldType == 'integer' || fieldType == 'percent' || fieldType == 'currency' || fieldType == 'double' || fieldType == 'long';            
            columns.add(getMetadataColumn(fullFieldName, isNumber));
        }
        columns.add(getMetadataColumn('CUST_NAME', false)); // seems to be the format for getting the object's name field
        for (MetadataService.ReportColumn column : columns)
            System.debug('column = '+ column);
        if (primaryGrouping != null) {
            MetadataService.ReportBucketField bucket = getMetadataBucket(fakeObjRes.getName() + '.'+ fakeObjectFields.get('primaryGrouping'), primaryGrouping, 0);
            buckets.add(bucket);
            groupings.add(getMetadataGrouping(bucket.developerName));
            //chart.groupingColumn = bucket.developerName;
        }
        System.debug('secondaryGrouping = '+ secondaryGrouping);
        if (secondaryGrouping != null) {
            MetadataService.ReportBucketField bucket = getMetadataBucket(fakeObjRes.getName() +'.'+ fakeObjectFields.get('secondaryGrouping'), secondaryGrouping, 1);
            buckets.add(bucket);
            groupings.add(getMetadataGrouping(bucket.developerName));
            //chart.secondaryGroupingColumn = bucket.developerName;
        }
        for (MetadataService.ReportBucketField bucket : buckets)
            System.debug('bucket = '+ bucket.masterLabel +', '+ bucket.sourceColumnName +', '+ bucket.developerName);            

        aggregates.add(getFormulaColumn(metricName, metricType));
        filter = getMetadataFilter(reportName);
        /* End metadata processing */

        newReport.type = 'Report';  // type of metadata
        newReport.reportType = 'CustomEntity$' + fakeObjRes.getName(); // data source, i.e. sobject(s)
        newReport.name = reportName.left(apiNameMaxLength);
        newReport.folderName = folderName;
        newReport.fullName = folderName +'/Fake'+ Datetime.now().getTime();
        newReport.columns = columns; // public MetadataService.ReportColumn[] columns;
        newReport.buckets = buckets; // public MetadataService.ReportBucketField[] buckets;
        newReport.chart = chart; // public MetadataService.ReportChart chart;
        newReport.groupingsDown = groupings; // MetadataService.ReportGrouping[]
        newReport.filter = filter; // MetadataService.ReportFilter
        newReport.format = Reports.ReportFormat.SUMMARY.name();
        newReport.scope = 'organization';   // no idea what this does, but it seems to work
        newReport.showDetails = true;   // personal preference
        newReport.aggregates = aggregates; //public MetadataService.ReportAggregate[] aggregates;

        System.debug('newReport = '+ newReport);
        // Create the report clone
        MetadataService.SaveResult result = service.createMetadata(new MetadataService.Metadata[] { newReport })[0];
        System.debug('final save result = '+ result);
        // Handle results
        handleSaveResults(result);
        return result;
        
    }


    /* The following section is customized adapters based on the MetadataService class  */
    public static MetadataService.ReportColumn getMetadataColumn(String fullFieldName, boolean isNumber) {
        MetadataService.ReportColumn newColumn = new MetadataService.ReportColumn();
        newColumn.showChanges = null;
        newColumn.reverseColors = null;
        newColumn.field = fullFieldName;
        newColumn.aggregateTypes = isNumber ? new String[] {'Sum', 'Average'} : null;
        return newColumn;
    }
    

    public static MetadataService.ReportBucketField getMetadataBucket(String fullFieldName, String label, Integer jankyUniqueCharacter) {
        MetadataService.ReportBucketField newBucket = new MetadataService.ReportBucketField();
        newBucket.values = null;
        newBucket.useOther = false;
        newBucket.sourceColumnName = fullFieldName;
        newBucket.otherBucketLabel = null;
        newBucket.nullTreatment = 'n';
        newBucket.masterLabel = label;
        newBucket.developerName = 'BucketField_'+ String.valueOf(jankyUniqueCharacter) + Datetime.now().getTime();
        newBucket.bucketType = 'text';
       return newBucket;
    }

    public static MetadataService.ReportGrouping getMetadataGrouping(String fieldDeveloperName) {
        MetadataService.ReportGrouping newGrouping = new MetadataService.ReportGrouping();
        newGrouping.sortType = null;
        newGrouping.sortOrder = 'Asc';
        newGrouping.sortByName = null;
        newGrouping.field = fieldDeveloperName;
        newGrouping.dateGranularity = 'Day';
        newGrouping.aggregateType = 'Sum';
        return newGrouping;
    }

    public static MetadataService.ReportFilter getMetadataFilter(String reportName) {
        MetadataService.ReportFilterItem newFilterItem = new MetadataService.ReportFilterItem();
        newFilterItem.column = fakeObjRes.getName() + '.Group__c';
        newFilterItem.isUnlocked = true;
        newFilterItem.operator = 'equals';
        newFilterItem.value = reportName;
        MetadataService.ReportFilterItem[] newFilterItems = new List<MetadataService.ReportFilterItem>{newFilterItem};

        MetadataService.ReportFilter newFilter = new MetadataService.ReportFilter();
        newFilter.criteriaItems = newFilterItems;
        return newFilter;
    }

    public static MetadataService.ReportAggregate getFormulaColumn(String label, String datatype) {
        if(datatype == null) {
            datatype = 'number';
        }
        MetadataService.ReportAggregate agg = new MetadataService.ReportAggregate();
        agg.calculatedFormula = fakeObjRes.getName() +'.'+ fakeObjectFields.get('value') +':SUM';
        agg.datatype = datatype;
        agg.developerName = 'FORMULA1'; // note: must start with 'FORMULA'
        //agg.downGroupingContext = 'ALL_SUMMARY_LEVELS';
        //agg.downGroupingContext = 'GRAND_SUMMARY';
        agg.isActive = true;
        agg.masterLabel = label;  
        return agg;  
    }
    
    // Needs to be called from VisualForce page, not LWC (will not work if @AuraEnabled)
    public static MetadataService.MetadataPort createService()
    {
        System.debug('in createService()');
        MetadataService.MetadataPort service = new MetadataService.MetadataPort();
        service.SessionHeader = new MetadataService.SessionHeader_element();
        service.SessionHeader.sessionId = UserInfo.getSessionId();
        return service;
    }

    /** (copied directly from MetadataService.cls)
     * Example helper method to interpret a SaveResult, throws an exception if errors are found
     **/
    public static void handleSaveResults(MetadataService.SaveResult saveResult)
    {
        // Nothing to see?
        if(saveResult==null || saveResult.success)
            return;
        // Construct error message and throw an exception
        if(saveResult.errors!=null)
        {
            List<String> messages = new List<String>();
            messages.add(
                (saveResult.errors.size()==1 ? 'Error ' : 'Errors ') +
                    'occured processing component ' + saveResult.fullName + '.');
            for(MetadataService.Error error : saveResult.errors) {
                //messages.add('extended results: '+ error.ExtendedErrorDetails);
                messages.add(
                    error.message + ' (' + error.statusCode + ').' +
                    ( error.fields!=null && error.fields.size()>0 ?
                        ' Fields ' + String.join(error.fields, ',') + '.' : '' ) );
            }
            if(messages.size()>0)
                throw new MetadataServiceExamplesException(String.join(messages, ' '));
        }
        if(!saveResult.success)
            throw new MetadataServiceExamplesException('Request failed with no specified error.');
    }

}