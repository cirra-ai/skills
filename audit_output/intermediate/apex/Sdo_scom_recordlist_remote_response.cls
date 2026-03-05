/**
* @author Vinay C N
* @date 
* @description : Generic Class to handle server trip for apex. 
Modification Log:
------------------------------------------------------------------------------------
Developer Mod Number Date Description
------------------------------------------------------------------------------------
*/
public class Sdo_scom_recordlist_remote_response{
    
    @AuraEnabled
    public Boolean isSuccess;
    @AuraEnabled
    public String message;
    @AuraEnabled
    public Integer statusCode;
    @AuraEnabled
    public Object payload;
    
    public Sdo_scom_recordlist_remote_response(Boolean isSuccess, String message, Object data) {
        this.isSuccess = isSuccess;
        this.message = message;
        this.payload = data;
    }

    public Sdo_scom_recordlist_remote_response(Boolean isSuccess,Integer statusCode, String message, Object data) {
        this.isSuccess = isSuccess;
        this.message = message;
        this.statusCode = statusCode;
        this.payload = data;
    }
    
    public Sdo_scom_recordlist_remote_response(Object data) {
        this(true, 'Done.', data);
    }
}