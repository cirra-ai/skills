public class AgentListController {

    public Map<String, AI_Agent_Label__mdt> labels {get; set;}
    // List of all the AI Agents to display
    public List<AI_Agent__c> listOfAgents {get; set;}
    public Decimal countOfConversations {get; set;}
    public String currentAgent {get; set;}
    public String selectedAgentId {get; set;}
    public String conversationActionedId {get; set;}
	public String currentSortOrder;
    public String sortOrder {get; set;}
    public Boolean isReverseOrder = false;
    public AIAgentConversationComparator.SortOrder order;
    // Quickly get the list of conversations by AI Agent for the filters
    public Map<String, List<AI_Agent_Conversation__c>> conversationMap {get; set;}
    // Full list to swap back to if we change filters
    public List<AI_Agent_Conversation__c> fullConversationList {get; set;}
    // List displayed on the screen
    public List<AI_Agent_Conversation__c> conversationlist {get; set;}

    public AgentListController() {
        // Load all AI Agent Conversations and put them into a Map, with the parent AI Agent ID as the Id.
        labels = AI_Agent_Label__mdt.getAll();
        conversationMap = new Map<String, List<AI_Agent_Conversation__c>>();
        conversationlist = new List<AI_Agent_Conversation__c>();
        fullConversationList = new List<AI_Agent_Conversation__c>();
		countOfConversations = 0;
        currentAgent = 'All';
        currentSortOrder = 'Flag';
        order = AIAgentConversationComparator.SortOrder.DEFAULT_ORDER;
        listOfAgents = [SELECT Id, Name, Num_Conversations__c FROM AI_Agent__c where Display_Agent__c = true Order by Num_Conversations__c  desc];
        // Find the total number of conversations across all of the agents
        for (AI_Agent__c agent : listOfAgents)
        {
            countOfConversations += agent.Num_Conversations__c;
        }

        for (AI_Agent_Conversation__c conv : [SELECT AI_Agent__c, AI_Agent_Name__c, Name, Flag__c, Summary__c, Conversation_Start_Seconds__c, Conversation_Start_Date__c, Flag_Reason__c, isHidden__c  FROM AI_Agent_Conversation__c WHERE AI_Agent__r.Display_Agent__c = TRUE ORDER BY Flag__c DESC, Conversation_Start_Seconds__c DESC])
        {
            if(!conversationMap.containsKey(conv.AI_Agent__c)) {
                conversationMap.put(conv.AI_Agent__c, new List<AI_Agent_Conversation__c>());
            }
            conversationMap.get(conv.AI_Agent__c).add(conv);
            conversationlist.add(conv);
            fullConversationList.add(conv);
        }
    }

    public AgentListController(ApexPages.StandardController sc) {
        this();
    }

    public List<AI_Agent_Conversation__c> getAIAgentConversations(Id aiAgentId)
    {
        if(conversationMap.containsKey(aiAgentId)) {
            return conversationMap.get(aiAgentId);
        }
        // If not found, return all conversations
        return conversationlist;
    }

    public PageReference updateAIAgentConversations()
    {
        // Repopulate the conversation list with new values
        System.debug('updateAIAgentConversations called, with currentAgent = ' + currentAgent + ', selectedAgentId = ' + selectedAgentId);
        if (currentAgent != selectedAgentId)
        {
            conversationlist.clear();
            System.debug('Cleared the list');
            if(conversationMap.containsKey(selectedAgentId)) {
                // Show just the conversations for the given Agent ID
                System.debug('Adding conversations for selected Agent');
                // Reorder the list in case it has changed since it was last shown
				conversationMap.get(selectedAgentId).sort(new AIAgentConversationComparator(this.order,this.isReverseOrder));
                conversationlist.addAll(conversationMap.get(selectedAgentId));
            }
            else {
                // Show all conversations
                System.debug('Adding all to the list');
                // Reorder the list in case it has changed since it was last shown
                fullConversationList.sort(new AIAgentConversationComparator(this.order,this.isReverseOrder));
                conversationlist.addAll(fullConversationList);
            }
        }
        currentAgent = selectedAgentId;
        return null;
    }

    public PageReference lowerFlagForConversation()
    {
        // Repopulate the conversation list with new values
        System.debug('lowerFlagForConversation called, with conversationActionedId = ' + conversationActionedId);
        String agentId = null;
		// Lower the flag (in memory only, reloaded on page refresh)
        for (AI_Agent_Conversation__c conv : conversationlist) {
            System.debug('Comparing against ' + conv.Id);
            if (Id.valueOf(conv.Id) == conversationActionedId ) {
                conv.Flag__c = false;
                agentId = conv.AI_Agent__c;
            }
        }
		// Re-order the currently displayed list. Others will be reordered when needed
        conversationlist.sort(new AIAgentConversationComparator(this.order,this.isReverseOrder));
        return null;
    }

    public PageReference reorderList()
    {
        // Repopulate the conversation list with new values
        System.debug('reorderList called, with sortOrder = ' + sortOrder + ', reversed? ' + this.isReverseOrder);
        if (currentSortOrder == sortOrder)
        {
            this.isReverseOrder = !this.isReverseOrder; // Flip ordering
        }
        else {
            // We've change what we're ordering by so use default order
            if (sortOrder == 'Flag') {
                order = AIAgentConversationComparator.SortOrder.DEFAULT_ORDER;
            } else if (sortOrder == 'Name') {
                order = AIAgentConversationComparator.SortOrder.AGENT_NAME;
            } else if (sortOrder == 'Summary') {
                order = AIAgentConversationComparator.SortOrder.CONVERSATION_SUMMARY;
            } else if (sortOrder == 'Length') {
                order = AIAgentConversationComparator.SortOrder.LONGEST_CONVERSATION;
            }
            currentSortOrder = sortOrder;
        }
		// Re-order the lists
		System.debug('Ordering list with sortOrder = ' + sortOrder + ', reversed? ' + this.isReverseOrder);
        conversationlist.sort(new AIAgentConversationComparator(this.order,this.isReverseOrder));
        return null;
    }

    public PageReference removeConversation()
    {
        // Repopulate the conversation list with new values
        System.debug('removeConversation called, with conversationActionedId = ' + conversationActionedId);
		// Remove the Conversation (in memory only, reloaded on page refresh)
		String agentId = null;
        for (AI_Agent_Conversation__c conv : conversationlist) {
            System.debug('Comparing against ' + conv.Id);
            if (Id.valueOf(conv.Id) == conversationActionedId ) {
                conv.isHidden__c = true;
                agentId = conv.AI_Agent__c;
                break;
            }
        }
        countOfConversations = countOfConversations - 1;

        for (AI_Agent__c agent : listOfAgents) {
            if (agent.Id == agentId){
                //TODO: find a way to edit the value that is shown for number of conversations for each agent
                //agent.Num_Conversations__c--;
            }
        }

        return null;
    }

}