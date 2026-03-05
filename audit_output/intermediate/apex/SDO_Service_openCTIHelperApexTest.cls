@isTest(SeeAllData=true)
public class SDO_Service_openCTIHelperApexTest {
    public static testMethod void doTest() {
        Account myAcc = [SELECT Id, Name FROM Account ORDER BY Name ASC LIMIT 1];

        Contact con = new Contact();
        con.AccountId = myAcc.Id;
        con.LastName = 'myLastName';
        con.FirstName = 'myFirstName';
        insert con;

        SDO_Service_openCTIHelperApex helper = new SDO_Service_openCTIHelperApex();

        Contact myContact = SDO_Service_openCTIHelperApex.getContactViaId(con.Id);

        SDO_Service_openCTIHelperApex.createMyConfig('ContactName', 'AccountName', myContact.Id, myAcc.Id, 'CEO', '5555555', true, true);
    }
}