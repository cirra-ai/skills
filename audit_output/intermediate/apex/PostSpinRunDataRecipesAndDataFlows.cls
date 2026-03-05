public class PostSpinRunDataRecipesAndDataFlows {
    
    public static void runAllDataRecipe() {
        String connectorId;
        String dataflowId;
        String baseURL = System.URL.getOrgDomainURL().toExternalForm();
        HttpRequest req = new HttpRequest();
        HttpResponse res = new HttpResponse();
        Http http = new Http();
        
        req.setEndpoint(baseURL+'/services/data/v57.0/wave/recipes');
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        
        try {
            res = http.send(req);
            System.debug(res.getBody());
            Map<String, Object> jsonMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> recipes = (List<Object>) jsonMap.get('recipes');
            
            String recipeId = null;
            String recipeURL = null;
            
            //run all of them
            for (Object recipe : recipes) {
                Map<String, Object> recipeMap = (Map<String, Object>) recipe;
                String label = (String) recipeMap.get('label');
                
                recipeId = (String) recipeMap.get('id');
                dataflowId = (String) recipeMap.get('targetDataflowId');
                runDataFlow(dataflowId, baseURL);
        
                }
            }
                catch (System.CalloutException e) {
            System.debug('Callout error: ' + e);
        }
    }

     public static void runAllDataflows() {
        String connectorId;
        String dataflowId;
        String baseURL = System.URL.getOrgDomainURL().toExternalForm();
        HttpRequest req = new HttpRequest();
        HttpResponse res = new HttpResponse();
        Http http = new Http();
        
        req.setEndpoint(baseURL+'/services/data/v57.0/wave/dataflows');
        req.setMethod('GET');
        req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
        
        try {
            res = http.send(req);
            System.debug(res.getBody());
            Map<String, Object> jsonMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            List<Object> recipes = (List<Object>) jsonMap.get('dataflows');
            
            String recipeId = null;
            String recipeURL = null;
            
            //run all of them
            for (Object recipe : recipes) {
                Map<String, Object> datafloweMap = (Map<String, Object>) recipe;
                dataflowId = (String) datafloweMap.get('id');
                runDataFlow(dataflowId, baseURL);
                }
            }
                catch (System.CalloutException e) {
            System.debug('Callout error: ' + e);
        }
    }
    
        public static void runDataFlow(String targetDataFlowId, String baseURL){
            Http h = new Http();    
            HttpRequest req = new HttpRequest();
            req.setEndpoint(baseURL+'/services/data/v57.0/wave/dataflowjobs');
            req.setMethod('POST');
            req.setHeader('Authorization', 'Bearer ' + UserInfo.getSessionId());
            req.setHeader('Content-Type', 'application/json');
           
            //req.setBody('{"dataflowId": "'+targetDataFlowId +'","command": "start"}');
           req.setBody('{"dataflowId": "'+targetDataFlowId+'","command": "start"}'); 
            System.debug('req = '+req);
            
            // Send the request, and return a response
            HttpResponse res = h.send(req);
            System.debug(res);
        
        
    }
}