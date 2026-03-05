global class SDO_Community_ArticlePagedResult {
    @AuraEnabled
    public Integer pageSize { get;set; }
    @AuraEnabled
    public Integer page { get;set; }
    @AuraEnabled
    public Integer total { get;set; }
    @AuraEnabled
    public List<KnowledgeArticleVersion> articles { get;set; }
}