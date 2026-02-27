import streamlit as st
import yaml

def render_tuning_panel():
    st.header("🎛 Hyperparameter Tuning")

    lr = st.slider("Learning Rate", 1e-5, 1e-2, 1e-4)
    batch_size = st.selectbox("Batch Size", [16, 32, 64])
    num_layers = st.slider("Transformer Layers", 2, 12, 6)

    config = {
        "lr": lr,
        "batch_size": batch_size,
        "num_layers": num_layers
    }

    if st.button("Save Config"):
        with open("training_pipeline/config.yaml", "w") as f:
            yaml.dump(config, f)

        st.success("Config Saved.")