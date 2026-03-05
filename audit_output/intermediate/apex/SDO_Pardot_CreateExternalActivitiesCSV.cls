public class SDO_Pardot_CreateExternalActivitiesCSV {
    public String prospectEmails { get; set; }
    public String businessUnitId { get; set; }
    public String activityValues { get; set; }
    public String activityTypes { get; set; }
    public String extensionName { get; set; }
    public Integer numExternalActivities { get; set;}
    List<String> listActivityTypes = new list<String>();
    List<String> listActivityValues = new list<String>();
    List<String> listProspectEmails = new list<String>();
    List<String> listExternalActivities = new list<String>();
    public PageReference create() {
        listActivityTypes = activityTypes.split(',');
        listActivityValues = activityValues.split(',');
        listProspectEmails = prospectEmails.split(',');
        pagereference ref = new pagereference('/apex/SDO_Pardot_CreateExternalActivitiesCSV');
        ref.setredirect(true);
        createExternalActivitiesCsv();
        return ref;
    }
    
    private void createExternalActivitiesCsv() {
        String externalActivities = 'ExtensionName, Activity Type, Prospect Email, Activity Value\n';
        for(Integer i = 0; i < numExternalActivities; i++){
            String activityRow = extensionName + ',' + getRandomString(listActivityTypes) + ',' + getRandomString(listProspectEmails) + ',' + getRandomString(listActivityValues) + '\n';
            externalActivities = externalActivities + activityRow;
        } 
        ContentVersion conVer = new ContentVersion();
        conVer.ContentLocation = 'S'; // S specifies this document is in Salesforce, E is for external files
        conVer.PathOnClient = 'ExternalActivities.csv';
        conVer.Title = 'External Activities';
        conVer.VersionData = Blob.valueOf(externalActivities);
        insert conVer;
    }
    
    private String getRandomString(List<String> inputValues) {
        Integer listSize = inputValues.size();
        Integer randomNumber = Math.mod(Math.abs(Crypto.getRandomLong().intValue()),listSize);
        String randomString= inputValues[randomNumber];
        return randomString;
    }
}