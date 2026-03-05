public class PostSpinRunDataSync {
    
    public static void getConnector() {
        String connectorId;
        String baseURL = System.URL.getOrgDomainURL().toExternalForm();
        HttpRequest req = new HttpRequest();
        HttpResponse res = new HttpResponse();
        Http http = new Http();

        req.setEndpoint(baseURL+'/services/data/v57.0/wave/dataConnectors');
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        boolean continueProcessing =true;

        try 
        {
            res = http.send(req);
            System.debug(res.getBody());
            if(!res.getBody().contains('FUNCTIONALITY_NOT_ENABLED'))
            {
                Map<String, Object> jsonMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
                List<Object> connectors = (List<Object>) jsonMap.get('dataConnectors');
                
                //run all of them
                for (Object connector : connectors) 
                {
                    Map<String, Object> connectorMap = (Map<String, Object>) connector;
                    
                    connectorId = (String) connectorMap.get('id');
                    runDataSync(connectorId,baseURL);
                }
            }
            else
            {
                continueProcessing=false;    
            }    
            
        } 
        catch (System.CalloutException e) {
            System.debug('Callout error: ' + e);
            continueProcessing=false;
        }
    }
    
    
    public static void runDataSync(String conID, String baseURL){
        Http h = new Http();    
        HttpRequest req = new HttpRequest();
        req.setEndpoint(baseURL+'/services/data/v57.0/wave/dataConnectors/'+conId+'/ingest');
        req.setMethod('POST');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        req.setBody('{}');
        
        // Send the request, and return a response
        HttpResponse res = h.send(req);
        System.debug(res);
    }
}