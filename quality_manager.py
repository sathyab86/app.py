class QualityCapability:
    def __init__(self, name: str, category: str, scoring_criteria: dict):
        self.name = name
        self.category = category
        self.scoring_criteria = scoring_criteria

class QualityCapabilityManager:
    def __init__(self):
        self.capabilities = {}
        self._initialize_base_capabilities()
    
    def _initialize_base_capabilities(self):
        # Manufacturing Quality Capabilities
        self.add_capability(
            "QMS",
            "Quality Management System",
            "System",
            {
                "1": "No formal QMS",
                "3": "Basic quality procedures",
                "5": "ISO 9001 implementation in progress",
                "7": "ISO 9001 certified",
                "10": "Advanced integrated QMS with multiple certifications"
            }
        )
        # Add other base capabilities here...
    
    def add_capability(self, id: str, name: str, category: str, scoring_criteria: dict):
        """Add a new quality capability"""
        self.capabilities[id] = QualityCapability(name, category, scoring_criteria)
    
    def remove_capability(self, id: str):
        """Remove a quality capability"""
        if id in self.capabilities:
            del self.capabilities[id]
    
    def edit_capability(self, id: str, name: str = None, category: str = None, scoring_criteria: dict = None):
        """Edit an existing quality capability"""
        if id in self.capabilities:
            cap = self.capabilities[id]
            if name:
                cap.name = name
            if category:
                cap.category = category
            if scoring_criteria:
                cap.scoring_criteria = scoring_criteria
    
    def get_capabilities_by_category(self, category: str) -> dict:
        """Get all capabilities in a specific category"""
        return {id: cap for id, cap in self.capabilities.items() if cap.category == category}
    
    def get_all_categories(self) -> list:
        """Get list of all unique categories"""
        return list(set(cap.category for cap in self.capabilities.values()))
