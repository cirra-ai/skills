@IsTest
public class OMSToolsFlowStringToArrayTest {
    @isTest
    static void testToolsFlowStringToArray(){
        List<String> testString = new List<String>{'a,b,c'};
        List<List<String>> testArray = OMSToolsFlowStringToArray.ConvertStringToArray(testString);
        System.assertEquals(3, testArray[0].size());

        testString = new List<String>{'a;b;c'};
        testArray = OMSToolsFlowStringToArray.ConvertStringToArray(testString);
        System.assertEquals(3, testArray[0].size());
    }
}