global class SDO_Service_BotsGetBotMessage {
    @InvocableMethod(label='Einstein Chatbots - Get random Bot Message by Type')
    global static List<SDO_Service_Bot_Message__c> getBotMessage(List<String> inputs)
    {
        for (String input : inputs){
            System.debug('XXXXX Input is ' + input);
            if (input!=null){
                List<SDO_Service_Bot_Message__c> result = new List<SDO_Service_Bot_Message__c>();
                List<SDO_Service_Bot_Message__c> messageList = [SELECT Id, Message_1__c, Message_2__c, Name from SDO_Service_Bot_Message__c where Type__c = :input];
                Integer rand = math.round(math.random()*1000);  
                Integer position = math.mod(rand, messageList.size());
                SDO_Service_Bot_Message__c botMessage = messageList[position];
                result.add(botMessage);            
                return result;
            }
        }
        return new List<SDO_Service_Bot_Message__c>{new SDO_Service_Bot_Message__c()};
    }
}