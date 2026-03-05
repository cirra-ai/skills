/**
* @author Vinay C N
* @date 
* @description : To hold response
Modification Log:
------------------------------------------------------------------------------------
Developer Mod Number Date Description
------------------------------------------------------------------------------------
*/
public class Sdo_scom_recordlist_datatable_response{
        
    //to return list of sObject response 
    public List<sObject> lstDataTableData;
    //to return list of object response
    public List<Object> lstObjectData;
    //to return sObject
    public sObject tableData;  
    public Map<String,Object> maptoReturn;
    public Map<String, Map<String, String>> fieldNameToDetailsMap;
    public Map<String,String> iconPropertyMap;
    public Integer totalrecords;
    public Boolean isRelatedQuery;
    public String status;
        
    public Sdo_scom_recordlist_datatable_response(){
        lstDataTableData = new List<sObject>();
        lstObjectData = new List<object>();
        maptoReturn=new Map<String,Object>();
        fieldNameToDetailsMap = new Map<String, Map<String, String>>();
        iconPropertyMap = new Map<String,String>();
    }    
}