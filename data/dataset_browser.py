"""
Dataset Browser for Sign Language Data Visualization and Management
Interactive browser for exploring and managing sign language datasets
"""

import streamlit as st
import pandas as pd
import numpy as np
import cv2
import json
import os
from typing import Dict, List, Any, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class DatasetBrowser:
    """Interactive dataset browser for sign language data"""
    
    def __init__(self, data_dir: str, annotations_file: str):
        self.data_dir = data_dir
        self.annotations_file = annotations_file
        self.data = None
        self.current_index = 0
        self.filters = {}
        
        # Load data
        self.load_data()
    
    def load_data(self):
        """Load dataset annotations"""
        try:
            with open(self.annotations_file, 'r', encoding='utf-8') as f:
                if self.annotations_file.endswith('.json'):
                    self.data = json.load(f)
                else:
                    # Load CSV
                    self.data = pd.read_csv(f).to_dict('records')
            
            logger.info(f"Loaded {len(self.data)} samples")
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.data = []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dataset statistics"""
        if not self.data:
            return {}
        
        df = pd.DataFrame(self.data)
        
        stats = {
            'total_samples': len(df),
            'unique_glosses': df['gloss'].nunique() if 'gloss' in df.columns else 0,
            'unique_speakers': df['speaker_id'].nunique() if 'speaker_id' in df.columns else 0,
            'languages': df['language'].unique().tolist() if 'language' in df.columns else [],
            'avg_duration': df['duration'].mean() if 'duration' in df.columns else 0,
            'total_duration': df['duration'].sum() if 'duration' in df.columns else 0
        }
        
        return stats
    
    def filter_data(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to dataset"""
        if not self.data:
            return []
        
        filtered_data = self.data.copy()
        
        for key, value in filters.items():
            if value is None or value == '':
                continue
            
            if key == 'gloss':
                filtered_data = [item for item in filtered_data 
                              if value.lower() in str(item.get('gloss', '')).lower()]
            elif key == 'language':
                filtered_data = [item for item in filtered_data 
                              if item.get('language') == value]
            elif key == 'speaker_id':
                filtered_data = [item for item in filtered_data 
                              if item.get('speaker_id') == value]
            elif key == 'duration_range':
                min_dur, max_dur = value
                filtered_data = [item for item in filtered_data 
                              if min_dur <= item.get('duration', 0) <= max_dur]
        
        return filtered_data
    
    def get_sample_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Get sample by index"""
        if 0 <= index < len(self.data):
            return self.data[index]
        return None
    
    def create_streamlit_app(self):
        """Create Streamlit application"""
        st.set_page_config(
            page_title="Sign Language Dataset Browser",
            page_icon="🤟",
            layout="wide"
        )
        
        st.title("🤟 Sign Language Dataset Browser")
        st.markdown("---")
        
        # Sidebar for filters
        st.sidebar.header("Filters")
        
        # Gloss filter
        gloss_filter = st.sidebar.text_input("Gloss Search", "")
        
        # Language filter
        languages = self.get_unique_languages()
        selected_language = st.sidebar.selectbox(
            "Language", 
            ["All"] + languages,
            index=0
        )
        
        # Speaker filter
        speakers = self.get_unique_speakers()
        selected_speaker = st.sidebar.selectbox(
            "Speaker ID", 
            ["All"] + speakers,
            index=0
        )
        
        # Duration filter
        min_duration, max_duration = st.sidebar.slider(
            "Duration Range (seconds)",
            min_value=0.0,
            max_value=30.0,
            value=(0.0, 30.0),
            step=0.5
        )
        
        # Apply filters
        filters = {
            'gloss': gloss_filter if gloss_filter else None,
            'language': selected_language if selected_language != "All" else None,
            'speaker_id': selected_speaker if selected_speaker != "All" else None,
            'duration_range': (min_duration, max_duration)
        }
        
        filtered_data = self.filter_data(filters)
        
        # Main content
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.header("Dataset Overview")
            
            # Statistics
            stats = self.get_statistics()
            filtered_stats = self.get_filtered_statistics(filtered_data)
            
            # Display statistics
            st.subheader("Statistics")
            col1_1, col1_2, col1_3 = st.columns(3)
            
            with col1_1:
                st.metric("Total Samples", stats.get('total_samples', 0))
                st.metric("Filtered Samples", len(filtered_data))
            
            with col1_2:
                st.metric("Unique Glosses", stats.get('unique_glosses', 0))
            
            with col1_3:
                st.metric("Unique Speakers", stats.get('unique_speakers', 0))
            
            # Data table
            st.subheader("Data Samples")
            if filtered_data:
                df = pd.DataFrame(filtered_data)
                st.dataframe(df, height=300)
            else:
                st.warning("No data matches the current filters.")
        
        with col2:
            st.header("Sample Viewer")
            
            # Sample selector
            if filtered_data:
                sample_index = st.number_input(
                    "Sample Index",
                    min_value=0,
                    max_value=len(filtered_data) - 1,
                    value=0,
                    step=1
                )
                
                sample = filtered_data[sample_index]
                self.display_sample(sample)
            else:
                st.info("Select filters to view samples")
        
        # Visualizations
        st.header("Data Visualizations")
        
        if filtered_data:
            # Language distribution
            self.plot_language_distribution(filtered_data)
            
            # Duration distribution
            self.plot_duration_distribution(filtered_data)
            
            # Gloss frequency
            self.plot_gloss_frequency(filtered_data)
    
    def display_sample(self, sample: Dict[str, Any]):
        """Display individual sample"""
        st.subheader(f"Sample: {sample.get('id', 'Unknown')}")
        
        # Video preview
        if sample.get('video_path'):
            video_path = os.path.join(self.data_dir, sample['video_path'])
            if os.path.exists(video_path):
                # Extract first frame as preview
                cap = cv2.VideoCapture(video_path)
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    st.image(frame, caption="Video Preview", use_column_width=True)
        
        # Metadata
        st.subheader("Metadata")
        metadata = {
            "Gloss": sample.get('gloss', 'N/A'),
            "Text": sample.get('text', 'N/A'),
            "Language": sample.get('language', 'N/A'),
            "Speaker ID": sample.get('speaker_id', 'N/A'),
            "Duration": f"{sample.get('duration', 0):.2f}s",
            "FPS": sample.get('fps', 'N/A')
        }
        
        for key, value in metadata.items():
            st.write(f"**{key}:** {value}")
    
    def get_unique_languages(self) -> List[str]:
        """Get list of unique languages"""
        if not self.data:
            return []
        
        languages = set()
        for item in self.data:
            if item.get('language'):
                languages.add(item['language'])
        
        return sorted(list(languages))
    
    def get_unique_speakers(self) -> List[str]:
        """Get list of unique speaker IDs"""
        if not self.data:
            return []
        
        speakers = set()
        for item in self.data:
            if item.get('speaker_id'):
                speakers.add(item['speaker_id'])
        
        return sorted(list(speakers))
    
    def get_filtered_statistics(self, filtered_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics for filtered data"""
        if not filtered_data:
            return {}
        
        df = pd.DataFrame(filtered_data)
        
        return {
            'total_samples': len(df),
            'unique_glosses': df['gloss'].nunique() if 'gloss' in df.columns else 0,
            'unique_speakers': df['speaker_id'].nunique() if 'speaker_id' in df.columns else 0,
            'languages': df['language'].unique().tolist() if 'language' in df.columns else [],
            'avg_duration': df['duration'].mean() if 'duration' in df.columns else 0,
            'total_duration': df['duration'].sum() if 'duration' in df.columns else 0
        }
    
    def plot_language_distribution(self, data: List[Dict[str, Any]]):
        """Plot language distribution"""
        df = pd.DataFrame(data)
        
        if 'language' not in df.columns:
            return
        
        lang_counts = df['language'].value_counts()
        
        fig = px.pie(
            values=lang_counts.values,
            names=lang_counts.index,
            title="Language Distribution"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_duration_distribution(self, data: List[Dict[str, Any]]):
        """Plot duration distribution"""
        df = pd.DataFrame(data)
        
        if 'duration' not in df.columns:
            return
        
        fig = px.histogram(
            df, 
            x='duration',
            title="Duration Distribution",
            nbins=30,
            labels={'duration': 'Duration (seconds)'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def plot_gloss_frequency(self, data: List[Dict[str, Any]], top_n: int = 20):
        """Plot gloss frequency"""
        df = pd.DataFrame(data)
        
        if 'gloss' not in df.columns:
            return
        
        gloss_counts = df['gloss'].value_counts().head(top_n)
        
        fig = px.bar(
            x=gloss_counts.index,
            y=gloss_counts.values,
            title=f"Top {top_n} Most Frequent Glosses",
            labels={'x': 'Gloss', 'y': 'Frequency'}
        )
        
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)


class DatasetQualityAnalyzer:
    """Analyze dataset quality and identify issues"""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        self.df = pd.DataFrame(data) if data else pd.DataFrame()
    
    def analyze_missing_values(self) -> Dict[str, Any]:
        """Analyze missing values in dataset"""
        if self.df.empty:
            return {}
        
        missing_counts = self.df.isnull().sum()
        missing_percentages = (missing_counts / len(self.df)) * 100
        
        return {
            'missing_counts': missing_counts.to_dict(),
            'missing_percentages': missing_percentages.to_dict(),
            'total_samples': len(self.df)
        }
    
    def analyze_outliers(self, column: str = 'duration') -> Dict[str, Any]:
        """Analyze outliers in numerical columns"""
        if self.df.empty or column not in self.df.columns:
            return {}
        
        values = self.df[column].dropna()
        
        Q1 = values.quantile(0.25)
        Q3 = values.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = values[(values < lower_bound) | (values > upper_bound)]
        
        return {
            'column': column,
            'total_values': len(values),
            'outlier_count': len(outliers),
            'outlier_percentage': (len(outliers) / len(values)) * 100,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outlier_values': outliers.tolist()
        }
    
    def analyze_class_balance(self, class_column: str = 'gloss') -> Dict[str, Any]:
        """Analyze class balance"""
        if self.df.empty or class_column not in self.df.columns:
            return {}
        
        class_counts = self.df[class_column].value_counts()
        
        # Calculate balance metrics
        total_samples = len(self.df)
        num_classes = len(class_counts)
        
        # Gini coefficient for imbalance
        sorted_counts = sorted(class_counts.values)
        n = len(sorted_counts)
        cumsum = np.cumsum(sorted_counts)
        gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
        
        return {
            'column': class_column,
            'num_classes': num_classes,
            'total_samples': total_samples,
            'class_counts': class_counts.to_dict(),
            'min_class_samples': class_counts.min(),
            'max_class_samples': class_counts.max(),
            'imbalance_ratio': class_counts.max() / class_counts.min(),
            'gini_coefficient': gini
        }
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        report = {
            'dataset_overview': {
                'total_samples': len(self.df),
                'num_columns': len(self.df.columns),
                'columns': list(self.df.columns)
            },
            'missing_values': self.analyze_missing_values(),
            'outliers': self.analyze_outliers(),
            'class_balance': self.analyze_class_balance()
        }
        
        return report


def main():
    """Main function to run the dataset browser"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sign Language Dataset Browser")
    parser.add_argument("--data_dir", type=str, required=True, 
                       help="Path to dataset directory")
    parser.add_argument("--annotations", type=str, required=True,
                       help="Path to annotations file")
    
    args = parser.parse_args()
    
    # Create browser
    browser = DatasetBrowser(args.data_dir, args.annotations)
    
    # Run Streamlit app
    browser.create_streamlit_app()


if __name__ == "__main__":
    main()
