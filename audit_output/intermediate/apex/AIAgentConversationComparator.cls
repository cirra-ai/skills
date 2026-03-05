public class AIAgentConversationComparator implements Comparator<AI_Agent_Conversation__c> {

    // Ordering options - default is Flagged, then by length.
    private SortOrder order;
	private Boolean reverseOrder = false;

    public enum SortOrder {DEFAULT_ORDER,AGENT_NAME,CONVERSATION_SUMMARY,LONGEST_CONVERSATION}

    static final Integer DEFAULT_ORDER = 1;
    static final Integer AGENT_NAME = 2;
    static final Integer CONVERSATION_SUMMARY = 2;
    static final Integer LONGEST_CONVERSATION = 4;

    public AIAgentConversationComparator(){
        this.order = SortOrder.DEFAULT_ORDER;
    }

    public AIAgentConversationComparator(SortOrder fieldToOrder){
        this.order = fieldToOrder;
    }

    public AIAgentConversationComparator(SortOrder fieldToOrder, Boolean reverseOrder){
        this(fieldToOrder);
        this.reverseOrder = reverseOrder;
    }

    public Integer compare(AI_Agent_Conversation__c o1, AI_Agent_Conversation__c o2) {
        // The return value of 0 indicates that both elements are equal.
        Integer returnValue = 0;

        if(o1 == null && o2 == null) {
            returnValue = 0;
        } else if(o1 == null) {
            // nulls-first implementation
            returnValue = -1;
        } else if(o2 == null) {
            // nulls-first implementation
            returnValue = 1;
        }

        switch on this.order {
            when AGENT_NAME {
               if ((o1.AI_Agent_Name__c == null) && (o2.AI_Agent_Name__c == null)) {
                   // both have null Amounts
                   returnValue = 0;
               } else if (o1.AI_Agent_Name__c == null){
                   // nulls-first implementation
                   returnValue = -1;
               } else if (o2.AI_Agent_Name__c == null){
                   // nulls-first implementation
                   returnValue = 1;
               } else {
                   returnValue = o1.AI_Agent_Name__c.compareTo(o2.AI_Agent_Name__c);
               }

                if (returnValue == 0)
                {
                    if ((o1.Conversation_Start_Seconds__c == null) && (o2.Conversation_Start_Seconds__c == null)) {
                        // both have null Amounts
                        returnValue = 0;
                    } else if (o1.Conversation_Start_Seconds__c == null){
                        // nulls-first implementation
                        returnValue = -1;
                    } else if (o2.Conversation_Start_Seconds__c == null){
                        // nulls-first implementation
                        returnValue = 1;
                    } else if (o1.Conversation_Start_Seconds__c < o2.Conversation_Start_Seconds__c) {
                        // Set return value to a negative value.
                        returnValue = 1;
                    } else if (o1.Conversation_Start_Seconds__c > o2.Conversation_Start_Seconds__c) {
                        // Set return value to a positive value.
                        returnValue = -1;
                    }
                }

            }
            when CONVERSATION_SUMMARY {
                if ((o1.Summary__c == null) && (o2.Summary__c == null)) {
                   // both have null Amounts
                   returnValue = 0;
               } else if (o1.Summary__c == null){
                   // nulls-first implementation
                   returnValue = -1;
               } else if (o2.Summary__c == null){
                   // nulls-first implementation
                   returnValue = 1;
               } else {
                   returnValue = o1.Summary__c.compareTo(o2.Summary__c);
               }

               // Fallback to longest conversation
               if (returnValue == 0)
               {
                   if ((o1.Conversation_Start_Seconds__c == null) && (o2.Conversation_Start_Seconds__c == null)) {
                       // both have null Amounts
                       returnValue = 0;
                   } else if (o1.Conversation_Start_Seconds__c == null){
                       // nulls-first implementation
                       returnValue = -1;
                   } else if (o2.Conversation_Start_Seconds__c == null){
                       // nulls-first implementation
                       returnValue = 1;
                   } else if (o1.Conversation_Start_Seconds__c < o2.Conversation_Start_Seconds__c) {
                       // Set return value to a negative value.
                       returnValue = 1;
                   } else if (o1.Conversation_Start_Seconds__c > o2.Conversation_Start_Seconds__c) {
                       // Set return value to a positive value.
                       returnValue = -1;
                   }
               }
            }
            when LONGEST_CONVERSATION {
                if ((o1.Conversation_Start_Seconds__c == null) && (o2.Conversation_Start_Seconds__c == null)) {
                    // both have null Amounts
                    returnValue = 0;
                } else if (o1.Conversation_Start_Seconds__c == null){
                    // nulls-first implementation
                    returnValue = -1;
                } else if (o2.Conversation_Start_Seconds__c == null){
                    // nulls-first implementation
                    returnValue = 1;
                } else if (o1.Conversation_Start_Seconds__c < o2.Conversation_Start_Seconds__c) {
                    // Set return value to a negative value.
                    returnValue = 1;
                } else if (o1.Conversation_Start_Seconds__c > o2.Conversation_Start_Seconds__c) {
                    // Set return value to a positive value.
                    returnValue = -1;
                }
            }
            when else {
                if (o1.Flag__c && !o2.Flag__c) {
                    returnValue = -1;
                } else if (!o1.Flag__c && o2.Flag__c) {
                    returnValue = 1;
                }
                else {
                    if ((o1.Conversation_Start_Seconds__c == null) && (o2.Conversation_Start_Seconds__c == null)) {
                        // both have null Amounts
                        returnValue = 0;
                    } else if (o1.Conversation_Start_Seconds__c == null){
                        // nulls-first implementation
                        returnValue = -1;
                    } else if (o2.Conversation_Start_Seconds__c == null){
                        // nulls-first implementation
                        returnValue = 1;
                    } else if (o1.Conversation_Start_Seconds__c < o2.Conversation_Start_Seconds__c) {
                        // Set return value to a negative value.
                        returnValue = 1;
                    } else if (o1.Conversation_Start_Seconds__c > o2.Conversation_Start_Seconds__c) {
                        // Set return value to a positive value.
                        returnValue = -1;
                    }
                }
            }

    	}
        if (this.reverseOrder)
        {
            // Flip the order, multiple by -1
            returnValue = returnValue * -1;
        }
        return returnValue;
    }

}