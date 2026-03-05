/** 
* =====================================================================================
* (c) Sixt GmbH, All rights reserved
* @className        GenericTestDataUtility 
* @author           Amanjot
* @email            amanjot.kaur@sixt.com
* @version          V0.1
* @date created     2019/07/24
* @last change      2019/07/24     Initial Version   
* @description      Utility class to create data for test classes
* =====================================================================================
*/
@isTest
public class Sdo_scom_recordlist_generic_datautility implements System.StubProvider{
    /* ===========================  Public methods =========================== */
    /**
     * @description create an sObject
     * @param       :  sObjectName         SObject   name of the sObject to be created
     * @return      :  sObject instance
     * @example 
     * Account a = (Account)GenericTestDataUtility.createSObject(new Account());
     */
    public static SObject createSObject(SObject sObjectName){
        return createSObject(sObjectName,new Map<String,Object>());
    }
    
    /**
     * @description :  create an sObject with a map to override field values
     * @param       :  sObjectName         SObject  name of the sObject to be created
     * @param       :  mapOfValuesOverride Map      map of values
     * @return sObject instance
     * @example 
     * Account acc = (Account)GenericTestDataUtility.createSObject(new Account(),new Map<String,Object>{
     *  'Description' => 'Test'
     * },false);
     */
    public static SObject createSObject(SObject sObjectName, Map<String,Object> mapOfValuesOverride){
        return createSObjectList(sObjectName,mapOfValuesOverride,1).get(0);
    }

    /**
     * @description create a list of sObjects
     * @param       :   sObjectName         SObject             name of the sObject to be created
     * @param       :   numberOfSObjects    Integer             number of sObjects to be created
     * @return list of sObject instances
     * @example 
     * List<Account> accList = GenericTestDataUtility.createSObjectList(new Account(),10);
     */
    public static List<SObject> createSObjectList(SObject sObjectName, Integer numberOfSObjects){
        return createSObjectList(sObjectName,new Map<String,Object>(),numberOfSObjects);
    }
    

    /**
     * @description create a list of sObjects with a map to override field values
     * @param       :   sObjectName         SObject             name of the sObject to be created
     * @param       :   mapOfValuesOverride Map<String,Object>  map of values
     * @param       :   numberOfSObjects    Integer             number of sObjects to be created
     * @param       :   doInsert            Boolean             if true the sObject list instances is inserted to the Salesforce database
     * @return list of sObject instances
     * @example 
     * List<Account> accList = GenericTestDataUtility.createSObjectList(new Account(),new Map<String,Object>{
     *  'Description' => 'Test'
     * },10,false);
     */    
    public static List<SObject> createSObjectList(SObject sObjectName,Map<String,Object> mapOfValuesOverride,Integer numberOfObjects) {
        List<SObject> sObjs = new List<SObject>();
        SObject newObj;
        newObj = addFieldDefaults(sObjectName,mapOfValuesOverride);
        // Clone the object the number of times requested. Increment the name field so each record is unique
        for (Integer i = 0; i < numberOfObjects; i++) {
            SObject clonedSObj = newObj.clone(false, true);           
            sObjs.add(clonedSObj);
        }
        
        return sObjs;
    }
    /**
     * @description create a map with fields and field values
     * @param       :   sObjectName         SObject             name of the sObject to be created
     * @param       :   mapOfValuesOverride Map<String,Object>  map of values
     * @return sObject instance
     */
    private static SObject addFieldDefaults(SObject sObj, Map<String, Object> defaults) {
        // Loop through the map of fields and if they are null on the object, fill them.
        for (String field : defaults.keySet()) {
            if (sObj.get(field) == null) {
                sObj.put(field, defaults.get(field));
            }
        }
        return sObj;
    }
    /**
     * @description create a user data
     * @param       :   inputParams Map<String,Object>  map of values
     * @return sObject User instance
     */  
    public static User createUser(){
        Profile p = [SELECT Id FROM Profile WHERE Name LIKE 'System%' LIMIT 1];  
        User u = new User();
        u.Alias = 'standt';
        u.UserName = 'standarduser1@test.com'; 
        u.Email = 'standarduser@test.com';
        u.EmailEncodingKey = 'UTF-8';
        u.LastName = 'Testing User';  
        u.LanguageLocaleKey = 'en_US';  
        u.LocaleSidKey = 'en_US';  
        u.ProfileId = p.Id;  
        u.TimeZoneSidKey = 'America/Los_Angeles';        
        return u;
    }  
    
    /**
     * @description :   create instance of GenericTestDataUtility
     * @return      :    GenericTestDataUtility  instance 
     */
     public static Sdo_scom_recordlist_generic_datautility getInstance() {
            return new Sdo_scom_recordlist_generic_datautility();
     }
     public static Map<String,Object> globalMethodNameToreturnValMap;
     
      /**
     * @description :   StubProvider is a callback interface,that requires implementing: handleMethodCall(). 
                         When a stubbed method is called, handleMethodCall() is called.
     * @param       :   stubbedMethodName    String           The name of the invoked method
     * @param       :   stubbedObject        Object           The stubbed Object
     * @param       :   returnType           Type             The return type of the invoked method
     * @param       :   listOfParamTypes     List<String>     A list of the parameter types of the invoked method
     * @param       :   listOfParamNames     List<String>     A list of the parameter names of the invoked method
     * @param       :   listOfArgs           List<Object>     The actual argument values passed into this method at runtime
     * @return list of sObject instances
     */ 
     public Object handleMethodCall(Object stubbedObject, String stubbedMethodName, 
        Type returnType, List<Type> listOfParamTypes, List<String> listOfParamNames, 
        List<Object> listOfArgs) {
        Object returnVal;
        for(String methodName:globalMethodNameToreturnValMap.keyset()){
            if(stubbedMethodName == methodName){
                returnVal=globalMethodNameToreturnValMap.get(methodName);
            }
        }
        return returnVal;
    }
     /**
     * @description create Mock of external class 
     * @param       :   Type                typeToMock          class to be mocked
     * @param       :   Object              valToReturn         value to be returned
     * @example 
     * MethodNameToreturnValMap.put('getDiscount',50);
     * MethodNameToreturnValMap.put('getNextStep','Hey!!');
     * DiscountsService mockDS = (DiscountsService)MockDiscountsService.createMock(DiscountsService.class,MethodNameToreturnValMap);
     * new OpportunitiesService(mockDS).createOpportunity(a.Id);
     */
     public static Object createMock(Type typeToMock,Map<String,Object> MethodNameToreturnValMap) {
        // mock class of typeToMock.
        // Invoke the stub API and pass it our mock provider to create a
        globalMethodNameToreturnValMap= MethodNameToreturnValMap.clone();
        return Test.createStub(typeToMock,Sdo_scom_recordlist_generic_datautility.getInstance());
    }
}