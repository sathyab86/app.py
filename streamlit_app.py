import streamlit as st
import json
import os
from datetime import datetime

def create_capability_management_ui(capability_manager):
    st.title("Quality Capability Management")
    
    # Add tabs for different management functions
    manage_tab, import_export_tab = st.tabs(["Manage Capabilities", "Import/Export"])
    
    with manage_tab:
        # Sidebar for navigation
        action = st.sidebar.radio(
            "Select Action",
            ["View All Capabilities", "Add New Capability", "Edit Capability", "Remove Capability"]
        )
        
        if action == "View All Capabilities":
            st.header("Current Capabilities")
            
            # Group capabilities by category
            categories = capability_manager.get_all_categories()
            
            for category in categories:
                st.subheader(f"Category: {category}")
                caps = capability_manager.get_capabilities_by_category(category)
                
                for cap_id, cap in caps.items():
                    with st.expander(f"{cap.name} ({cap_id})"):
                        st.write("**Category:** ", cap.category)
                        st.write("**Scoring Criteria:**")
                        for score, description in cap.scoring_criteria.items():
                            st.write(f"Level {score}: {description}")
        
        elif action == "Add New Capability":
            st.header("Add New Capability")
            
            # Input fields for new capability
            cap_id = st.text_input("Capability ID (no spaces)", key="new_cap_id")
            cap_name = st.text_input("Capability Name", key="new_cap_name")
            
            # Either select existing category or create new
            existing_categories = capability_manager.get_all_categories()
            use_existing = st.checkbox("Use existing category", value=True)
            
            if use_existing:
                cap_category = st.selectbox("Select Category", existing_categories)
            else:
                cap_category = st.text_input("New Category Name")
            
            # Dynamic scoring criteria input
            st.subheader("Scoring Criteria")
            scoring_criteria = {}
            
            for score in ["1", "3", "5", "7", "10"]:
                description = st.text_area(
                    f"Level {score} Description",
                    key=f"new_level_{score}"
                )
                if description:
                    scoring_criteria[score] = description
            
            if st.button("Add Capability"):
                if cap_id and cap_name and cap_category and scoring_criteria:
                    try:
                        capability_manager.add_capability(
                            cap_id,
                            cap_name,
                            cap_category,
                            scoring_criteria
                        )
                        st.success(f"Successfully added capability: {cap_name}")
                    except Exception as e:
                        st.error(f"Error adding capability: {str(e)}")
                else:
                    st.warning("Please fill in all required fields")
        
        elif action == "Edit Capability":
            st.header("Edit Capability")
            
            # Select capability to edit
            cap_id = st.selectbox(
                "Select Capability to Edit",
                list(capability_manager.capabilities.keys())
            )
            
            if cap_id:
                cap = capability_manager.capabilities[cap_id]
                
                # Edit fields
                new_name = st.text_input("Capability Name", value=cap.name)
                new_category = st.selectbox(
                    "Category",
                    capability_manager.get_all_categories(),
                    index=capability_manager.get_all_categories().index(cap.category)
                )
                
                # Edit scoring criteria
                st.subheader("Edit Scoring Criteria")
                new_scoring_criteria = {}
                
                for score in ["1", "3", "5", "7", "10"]:
                    default_desc = cap.scoring_criteria.get(score, "")
                    description = st.text_area(
                        f"Level {score} Description",
                        value=default_desc,
                        key=f"edit_level_{score}"
                    )
                    if description:
                        new_scoring_criteria[score] = description
                
                if st.button("Save Changes"):
                    try:
                        capability_manager.edit_capability(
                            cap_id,
                            name=new_name,
                            category=new_category,
                            scoring_criteria=new_scoring_criteria
                        )
                        st.success("Changes saved successfully")
                    except Exception as e:
                        st.error(f"Error saving changes: {str(e)}")
        
        elif action == "Remove Capability":
            st.header("Remove Capability")
            
            cap_id = st.selectbox(
                "Select Capability to Remove",
                list(capability_manager.capabilities.keys())
            )
            
            if cap_id:
                cap = capability_manager.capabilities[cap_id]
                
                st.warning(f"Are you sure you want to remove {cap.name} ({cap_id})?")
                st.write("This action cannot be undone.")
                
                if st.button("Confirm Removal"):
                    try:
                        capability_manager.remove_capability(cap_id)
                        st.success(f"Successfully removed capability: {cap_id}")
                    except Exception as e:
                        st.error(f"Error removing capability: {str(e)}")
    
    with import_export_tab:
        st.header("Import/Export Capabilities")
        
        # Export capabilities
        if st.button("Export Capabilities"):
            # Convert capabilities to JSON-serializable format
            export_data = {
                cap_id: {
                    "name": cap.name,
                    "category": cap.category,
                    "scoring_criteria": cap.scoring_criteria
                }
                for cap_id, cap in capability_manager.capabilities.items()
            }
            
            # Create JSON string
            json_str = json.dumps(export_data, indent=2)
            
            # Create download button
            st.download_button(
                label="Download Capabilities JSON",
                data=json_str,
                file_name=f"quality_capabilities_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        # Import capabilities
        st.subheader("Import Capabilities")
        uploaded_file = st.file_uploader(
            "Upload Capabilities JSON",
            type=["json"]
        )
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                
                # Preview import data
                st.write("Preview of capabilities to import:")
                st.json(import_data)
                
                if st.button("Confirm Import"):
                    for cap_id, cap_data in import_data.items():
                        capability_manager.add_capability(
                            cap_id,
                            cap_data["name"],
                            cap_data["category"],
                            cap_data["scoring_criteria"]
                        )
                    st.success("Capabilities imported successfully")
            except Exception as e:
                st.error(f"Error importing capabilities: {str(e)}")

# Add this to your main Streamlit app:
def main():
    st.set_page_config(layout="wide")
    
    # Initialize capability manager
    if 'capability_manager' not in st.session_state:
        st.session_state.capability_manager = QualityCapabilityManager()
    
    # Add a new tab for capability management
    tabs = st.tabs([
        "Data Collection",
        "Analysis",
        "Capability Management"
    ])
    
    with tabs[0]:
        # Your existing data collection UI
        pass
    
    with tabs[1]:
        # Your existing analysis UI
        pass
    
    with tabs[2]:
        create_capability_management_ui(st.session_state.capability_manager)

if __name__ == "__main__":
    main()
