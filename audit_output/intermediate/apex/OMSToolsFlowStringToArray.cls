global with sharing class OMSToolsFlowStringToArray {
    @InvocableMethod
    global static List<list<string>> ConvertStringToArray(List<string> values){
        if(!(values.isEmpty())){
            string tempStr = values[0];
            List<String> lstnew = tempStr.split(';');
            if(lstnew.size() == 1){
                lstnew = lstnew[0].split(',');
            }
            list<list<string>> finalLst = new list<list<string>>();
            finalLst.add(lstnew);
            return finalLst;
        }
        else return null;
    }
}