public class SDO_Service_CreateCases {
    
	@InvocableMethod(label='Create List of Cases' description='Creates a list of cases with the number passed in as the quantity in that list' category='Case')
    public static List<List<Id>> createListOfCases(List<Integer> numToCreate) {
        List<List<Id>> returnObj = new List<List<Id>>();
        
        
        for (Integer quantity : numToCreate) {
            List<Case> caseList = new List<Case>();
            for (Integer i = 0; i < quantity; i++) {
                Case newCase = new Case();
                newCase.Subject = 'Example case for Demos ' + (i + 1);   
                
                caseList.add(newCase);
            }
            
            insert caseList;
            List<Id> idList = new List<Id>();
            for (Case newCase : caseList) {
                idList.add(newCase.Id);
            }
            returnObj.add(idList);
        }
        
        return returnObj;
    }
}