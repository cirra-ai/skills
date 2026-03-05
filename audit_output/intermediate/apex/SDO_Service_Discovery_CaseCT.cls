public class SDO_Service_Discovery_CaseCT {
    @AuraEnabled
    public static Case getEDInfo(String caseId) {
        
        Case c = new Case();
        
        try {
            c = [SELECT SDO_Einstein_Discovery_Outcome__c, SDO_Einstein_Discovery_Leading_Causes__c, SDO_Einstein_Discovery_Prescription__c  
                     FROM Case
                     WHERE id =: caseId];
            
        } catch (Exception e) {
            System.debug('Case: ' + caseId);
        }
        return c;
    }
}