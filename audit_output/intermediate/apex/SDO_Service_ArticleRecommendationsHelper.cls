public class SDO_Service_ArticleRecommendationsHelper {
    public static String API_VERSION = 'v50.0';

    public class ArticleRecommendationsHelperInput {
        @InvocableVariable(label='Helper Config' description='All of the recommendations to use' required=true)
        public List<SDO_Service_Einstein_Agent_Helper__c> helperConfig;
        @InvocableVariable(label='Case' description='The case to predict fields on' required=true)
        public Case c;
    }


    @InvocableMethod(label='Create Demo Einstein Article Recommendation(s)' description='Creates mock Einstein Article recommendations for demo purposes.' category='Case')
    public static List<Id> createRecommendations(List<ArticleRecommendationsHelperInput> inputs){
        List<Id> articleIds = new List<Id>();
        for (ArticleRecommendationsHelperInput input : inputs) {
            Boolean addedResponse = false;
            Case c = input.c;
            List<SDO_Service_Einstein_Agent_Helper__c> helperConfig = input.helperConfig;
            DateTime now = DateTime.now();
            String currentTime = now.formatGmt('yyyy-MM-dd\'T\'HH:mm:ss\'Z\'');
            System.debug(currentTime);

            List<Map<String,Object>> compositeRequest = new List<Map<String,Object>>();
            List<KnowledgeArticleVersion> kavs = [Select Id, KnowledgeArticleId From KnowledgeArticleVersion];
            Map<String,String> kavIdMap = new Map<String,String>();

            for(KnowledgeArticleVersion kav: kavs){
                kavIdMap.put(kav.Id, kav.KnowledgeArticleId);
            }


            Integer referenceId = 1;

            for(SDO_Service_Einstein_Agent_Helper__c rule: helperConfig){
                if( c.get(rule.Field__c) != null){
                    String dataType = getType(c.get(rule.Field__c));
                    Boolean validRule = evaluateRule(dataType, c, rule);

                    if(validRule){

                        if (rule.Recommended_Article__c != null && kavIdMap.containsKey(rule.Recommended_Article__c)){
                            System.debug('SAVING ARTICLE RECOMMENDATION');
                            Map<String,Object> compositeRequestArticle = new Map<String,Object>();
                            String knowledgeId = kavIdMap.get(rule.Recommended_Article__c);
                            Map<String,Object> answerMetadata = new Map<String,Object>();
                            answerMetadata.put('luceneScore', rule.Recommended_Article_Score__c/100);
                            answerMetadata.put('answerRerankingScore', rule.Recommended_Article_Score__c/100);
                            answerMetadata.put('rankingPosition',0);
                            Map<String,Object> candidateAnswer = new Map<String,Object>{
                                'AnswerEntityId' => knowledgeId,
                                'IsRelevantCandidate' => true,
                                'AppSourceType' => 'ARTICLE_RECOMMENDATION',
                                'AnswerMetadata' => JSON.serialize(answerMetadata),
                                'QuestionId' => c.Id,
                                'RankingScore' => 80,
                                'RankingPosition' => 80};

                            compositeRequestArticle.put('url','/services/data/'+API_VERSION+'/sobjects/CandidateAnswer');
                            compositeRequestArticle.put('method', 'POST');
                            compositeRequestArticle.put('body', candidateAnswer);
                            compositeRequestArticle.put('referenceId', 'IncomingRecommendation'+referenceId);
                            referenceId++;
                            compositeRequest.add(compositeRequestArticle);
							// Add knowledge version ID to the list returned
                            //articleIds.add(knowledgeId);
                            addedResponse = true;
                            //break; can only add 1 article per call to this function
                        }
                    }
                }
            }

            if(compositeRequest.size() > 0){
                String sessionId = getSession();

                Map<String,Object> compositeRequestBody = new Map<String, Object>();
                compositeRequestBody.put('allOrNone',false);
                compositeRequestBody.put('compositeRequest', compositeRequest);

                Http http = new Http();
                HttpRequest req = new HttpRequest();
                req.setEndpoint(System.Url.getSalesforceBaseURL().toExternalForm() + '/services/data/'+API_VERSION+'/composite');
                req.setMethod('POST');
                req.setHeader('Authorization', 'Bearer ' + sessionId);
                req.setHeader('Content-Type', 'application/json');
                req.setHeader('Content-Length', '0');

                System.debug(compositeRequestBody);
                req.setBody(JSON.serialize(compositeRequestBody));

                HttpResponse res = http.send(req);
                String responseBody = res.getBody();
                List<String> responseParts = responseBody.split(',(?=\\{)');
                for(String rp: responseParts){
                    System.debug(rp);
                }
            }
            if (!addedResponse)
            {
                articleIds.add(null); // Fallback to add an entry so we have at least 1 per request
            }
        }
        return articleIds;
    }

    public static Boolean evaluateRule(String dataType, Case c, SDO_Service_Einstein_Agent_Helper__c rule){
        Boolean evaluation = false;
        System.debug('EVALUATING');

        //Gets messy since you cannot type dynamically. Move code up to cast before evaluation
        switch on rule.Comparator__c {
            when 'EQ' {
                System.debug('EQ');
                evaluation = c.get(rule.Field__c) == rule.Value__c;
            }
            when 'NOT_EQ' {
                System.debug('NOT EQ');
                evaluation = c.get(rule.Field__c) != rule.Value__c;
            }
            when 'STARTS' {
                System.debug('STARTS');
                String caseStringValue = String.valueOf(c.get(rule.Field__c));
                String ruleStringValue = String.valueOf(rule.Value__c);
                evaluation = caseStringValue.startsWithIgnoreCase(ruleStringValue);
            }
            when 'ENDS' {
                System.debug('ENDS');
                String caseStringValue = String.valueOf(c.get(rule.Field__c));
                String ruleStringValue = String.valueOf(rule.Value__c);
                evaluation = caseStringValue.endsWithIgnoreCase(ruleStringValue);
            }
            when 'CONTAINS'{
                System.debug('CONTAINS');
                String caseStringValue = String.valueOf(c.get(rule.Field__c));
                String ruleStringValue = String.valueOf(rule.Value__c);
                evaluation = caseStringValue.containsIgnoreCase(ruleStringValue);
            }
            when 'LT' {
                System.debug('LT');
                switch on dataType {
                    //insure proper typing
                    when 'Integer' {
                        evaluation = Integer.valueOf(c.get(rule.Field__c)) < Integer.valueOf(rule.Value__c);
                    }
                    when 'Double' {
                        evaluation = Double.valueOf(c.get(rule.Field__c)) < Double.valueOf(rule.Value__c);
                    }
                    when 'Date' {
                        evaluation = Date.valueOf(c.get(rule.Field__c)) < Date.valueOf(rule.Value__c);
                    }
                    when 'DateTime' {
                        evaluation = DateTime.valueOf(c.get(rule.Field__c)) < DateTime.valueOf(rule.Value__c);
                    }
                }
            }
            when 'LTE' {
                System.debug('LTE');
                switch on dataType {
                    //insure proper typing
                    when 'Integer' {
                        evaluation = Integer.valueOf(c.get(rule.Field__c)) <= Integer.valueOf(rule.Value__c);
                    }
                    when 'Double' {
                        evaluation = Double.valueOf(c.get(rule.Field__c)) <= Double.valueOf(rule.Value__c);
                    }
                    when 'Date' {
                        evaluation = Date.valueOf(c.get(rule.Field__c)) <= Date.valueOf(rule.Value__c);
                    }
                    when 'DateTime' {
                        evaluation = DateTime.valueOf(c.get(rule.Field__c)) <= DateTime.valueOf(rule.Value__c);
                    }
                }
            }
            when 'GTE' {
                System.debug('GTE');
                switch on dataType {
                    //insure proper typing
                    when 'Integer' {
                        evaluation = Integer.valueOf(c.get(rule.Field__c)) >= Integer.valueOf(rule.Value__c);
                    }
                    when 'Double' {
                        evaluation = Double.valueOf(c.get(rule.Field__c)) >= Double.valueOf(rule.Value__c);
                    }
                    when 'Date' {
                        evaluation = Date.valueOf(c.get(rule.Field__c)) >= Date.valueOf(rule.Value__c);
                    }
                    when 'DateTime' {
                        evaluation = DateTime.valueOf(c.get(rule.Field__c)) >= DateTime.valueOf(rule.Value__c);
                    }
                }
            }
            when 'GT' {
                System.debug('GT');
                switch on dataType {
                    //insure proper typing
                    when 'Integer' {
                        evaluation = Integer.valueOf(c.get(rule.Field__c)) > Integer.valueOf(rule.Value__c);
                    }
                    when 'Double' {
                        evaluation = Double.valueOf(c.get(rule.Field__c)) > Double.valueOf(rule.Value__c);
                    }
                    when 'Date' {
                        evaluation = Date.valueOf(c.get(rule.Field__c)) > Date.valueOf(rule.Value__c);
                    }
                    when 'DateTime' {
                        evaluation = DateTime.valueOf(c.get(rule.Field__c)) > DateTime.valueOf(rule.Value__c);
                    }
                }
            }
        }

        System.debug(evaluation);
        return evaluation;
    }

    //Login with a integrated user to get valid session id through SOAP
    //Lightning session id is not valid. Needs to exist before requests can execute
    //Default user is of alias ehelp // salesforce1
    public static String getSession(){
        User restUser = [Select Username From User Where (CommunityNickname = 'ehelp' Or Alias = 'ehelp') OR (FirstName = 'Einstein' AND LastName ='Helper') Limit 1];
        HttpRequest request = new HttpRequest();
        String endpoint = 'https://login.salesforce.com/services/oauth2/token';
        endpoint += '?grant_type=password';
        endpoint += '&client_id=3MVG9KsVczVNcM8zdoozgJaLPPYhYyCTdBF5O2FEjAShjwa.x7YBtZq1jm52I3mqom4QqIPMGs5Ww89tI7WDe';
        endpoint += '&client_secret=3636748017614097236';
        endpoint += '&username=' + restUser.Username;
        endpoint += '&password=salesforce1';
        request.setMethod('POST');

        request.setEndpoint(endpoint);
        HttpResponse res = (new Http()).send(request);
        System.debug(res);

        Map<String,Object> session = (Map<String,Object>)JSON.deserializeUntyped(res.getBody());
        return String.valueOf(session.get('access_token'));
    }

    //Fetch type without schema
    public static string getType(Object o) {
        if(o==null) return '';
        if(o instanceof SObject)            return ((SObject)o).getSObjectType().getDescribe().getName()+'';
        if(o instanceof Boolean)            return 'Boolean';
        if(o instanceof Id)                 return 'Id';
        if(o instanceof String)             return 'String';
        if(o instanceof Blob)               return 'Blob';
        if(o instanceof Date)               return 'Date';
        if(o instanceof Datetime)           return 'Datetime';
        if(o instanceof Time)               return 'Time';
        if(o instanceof String)             return 'String';
        if(o instanceof Integer)            return 'Integer';
        if(o instanceof Long)               return 'Long';
        if(o instanceof Decimal)            return 'Double';  // we can't distinguish between decimal and double
        if(o instanceof Double)             return 'Double';   // we can't distinguish between decimal and double
        if(o instanceof List<object>)       return 'List';
        return 'Object';                    // actually we can't detect maps and sets and maps
    }


}