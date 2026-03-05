public class SDO_FSL_KnowledgeContainer {
    @AuraEnabled
    public boolean attached {get; set;}
    @AuraEnabled
    public KnowledgeArticleVersion KnowledgeArticle {get; set;}
    
    public SDO_FSL_KnowledgeContainer() {        
    }
    
    public SDO_FSL_KnowledgeContainer(KnowledgeArticleVersion KnowledgeArticle) {
        this.attached = false;
        this.KnowledgeArticle = KnowledgeArticle;
    }
    
    public SDO_FSL_KnowledgeContainer(KnowledgeArticleVersion KnowledgeArticle, boolean attached) {
        this.attached = attached;
        this.KnowledgeArticle = KnowledgeArticle;
    }
}