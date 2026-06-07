"""Streamlit UI for RAG Data Preparation Toolkit."""

import streamlit as st
import os
import sys
import tempfile
import zipfile
import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from rag_data_toolkit.document_loader import is_word_document
from rag_data_toolkit.chunker import process_document
from rag_data_toolkit.exporters import EXPORTERS, CSV_COLUMNS
from rag_data_toolkit.eval_generator import generate_eval_samples, export_eval_samples

st.set_page_config(
    page_title="RAG Data Preparation Toolkit",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    for key, default in [
        ('processed_files', []),
        ('processing_complete', False),
        ('chunks', []),
        ('all_table_count', 0),
        ('all_image_count', 0),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


def create_output_directories():
    output_dir = PROJECT_ROOT / "streamlit_output"
    images_dir = PROJECT_ROOT / "extracted_images"
    output_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    return output_dir, images_dir


def save_uploaded_file(uploaded_file, temp_dir: Path) -> Path:
    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def extract_zip_files(zip_file, temp_dir: Path):
    word_files = []
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if is_word_document(file):
                    word_files.append(Path(root) / file)
    return word_files


def main():
    init_session_state()

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>  RAG Data Preparation Toolkit</h1>
        <p>Convert messy enterprise documents into section-aware, metadata-rich chunks for RAG knowledge bases.</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Export Format")
        export_format = st.selectbox(
            "Output format",
            options=list(EXPORTERS.keys()),
            format_func=lambda x: {"csv": "CSV", "jsonl": "JSONL", "dify": "Dify CSV"}[x],
            index=0,
        )

        st.header("Supported Input")
        st.markdown("- Word documents (.docx)")
        st.markdown("- ZIP archives (containing .docx)")

        st.header("Pipeline")
        st.markdown("1. Upload document")
        st.markdown("2. Configure parsing")
        st.markdown("3. Generate chunks")
        st.markdown("4. Preview output")
        st.markdown("5. Export data")

        st.header("Output")
        output_dir, images_dir = create_output_directories()
        if output_dir.exists():
            files = list(output_dir.glob("*"))
            if files:
                st.info(f"{len(files)} file(s) in output dir")

    # Main workflow
    tab_upload, tab_preview, tab_eval, tab_history = st.tabs([
        "Upload & Process", "Preview Output", "Eval Samples", "History"
    ])

    # --- Tab 1: Upload & Process ---
    with tab_upload:
        st.subheader("Step 1: Upload Documents")
        uploaded_files = st.file_uploader(
            "Drop Word documents or ZIP files here",
            type=['docx', 'zip'],
            accept_multiple_files=True,
            help="Max 200MB per file",
        )

        if uploaded_files:
            max_size = 200 * 1024 * 1024
            valid_files = [f for f in uploaded_files if f.size <= max_size]
            oversized = [f for f in uploaded_files if f.size > max_size]
            for f in oversized:
                st.error(f"{f.name} is too large ({f.size / 1024 / 1024:.1f}MB)")

            if valid_files:
                st.success(f"{len(valid_files)} file(s) ready for processing")

                st.subheader("Step 2: Configure")
                st.info(f"Export format: **{export_format.upper()}**")

                st.subheader("Step 3: Process")
                if st.button("Generate RAG-Ready Chunks", type="primary", use_container_width=True):
                    output_dir, images_dir = create_output_directories()

                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_path = Path(temp_dir)
                        all_word_files = []

                        progress = st.progress(0)
                        status = st.empty()

                        for i, uf in enumerate(valid_files):
                            status.text(f"Preparing {i+1}/{len(valid_files)}: {uf.name}")
                            if uf.name.endswith('.zip'):
                                zip_path = save_uploaded_file(uf, temp_path)
                                all_word_files.extend(extract_zip_files(zip_path, temp_path))
                            elif is_word_document(uf.name):
                                all_word_files.append(save_uploaded_file(uf, temp_path))
                            progress.progress((i + 1) / len(valid_files) / 3)

                        if not all_word_files:
                            st.error("No Word documents found.")
                            return

                        st.info(f"Found {len(all_word_files)} document(s)")

                        processed = []
                        all_chunks = []
                        for i, doc_path in enumerate(all_word_files):
                            status.text(f"Processing {i+1}/{len(all_word_files)}: {doc_path.name}")
                            try:
                                result = process_document(str(doc_path), str(output_dir), export_format)
                                if result:
                                    processed.append({'filename': doc_path.name, 'success': True, 'message': f"Processed: {doc_path.name} ({len(result)} chunks)"})
                                    all_chunks.extend(result)
                                else:
                                    processed.append({'filename': doc_path.name, 'success': False, 'message': f"Failed: {doc_path.name}"})
                            except Exception as e:
                                processed.append({'filename': doc_path.name, 'success': False, 'message': f"Error: {doc_path.name} — {e}"})
                            progress.progress(1/3 + (i + 1) / len(all_word_files) / 3)

                        status.text("Done")
                        progress.progress(1.0)

                        st.session_state.processed_files = processed
                        st.session_state.processing_complete = True
                        st.session_state.chunks = all_chunks
                        st.session_state.all_table_count = sum(1 for c in all_chunks if c.get('chunk_type') == 'table')
                        st.session_state.all_image_count = sum(1 for c in all_chunks if c.get('image_refs'))

                        # Summary metrics
                        st.subheader("Step 4: Results")
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Documents", len(processed))
                        with col2:
                            st.metric("Chunks", len(all_chunks))
                        with col3:
                            st.metric("Tables", st.session_state.all_table_count)
                        with col4:
                            st.metric("Images", st.session_state.all_image_count)
                        with col5:
                            export_files = len(list(output_dir.glob("*")))
                            st.metric("Export Files", export_files)

                        for p in processed:
                            (st.success if p['success'] else st.error)(p['message'])

                        # Step 5: Download
                        st.subheader("Step 5: Export")
                        _show_download_buttons(output_dir, images_dir, context="process")

    # --- Tab 2: Preview ---
    with tab_preview:
        st.subheader("Output Preview")
        if st.session_state.chunks:
            # Filters
            col_f1, col_f2, col_f3 = st.columns(3)
            chunks_df = pd.DataFrame(st.session_state.chunks)

            with col_f1:
                docs = ["All"] + sorted(chunks_df["document_name"].unique().tolist()) if "document_name" in chunks_df.columns else ["All"]
                filter_doc = st.selectbox("Document", docs)
            with col_f2:
                sections = ["All"] + sorted(chunks_df["section_path"].unique().tolist()[:50]) if "section_path" in chunks_df.columns else ["All"]
                filter_section = st.selectbox("Section", sections)
            with col_f3:
                types = ["All"] + sorted(chunks_df["chunk_type"].unique().tolist()) if "chunk_type" in chunks_df.columns else ["All"]
                filter_type = st.selectbox("Chunk Type", types)

            # Apply filters
            filtered = chunks_df.copy()
            if filter_doc != "All":
                filtered = filtered[filtered["document_name"] == filter_doc]
            if filter_section != "All":
                filtered = filtered[filtered["section_path"] == filter_section]
            if filter_type != "All":
                filtered = filtered[filtered["chunk_type"] == filter_type]

            st.info(f"Showing {len(filtered)} of {len(chunks_df)} chunks")

            # Preview columns
            preview_cols = [c for c in ['document_name', 'section_path', 'chunk_type', 'chunk_text'] if c in filtered.columns]
            if preview_cols:
                display_df = filtered[preview_cols].copy()
                if 'chunk_text' in display_df.columns:
                    display_df['chunk_text'] = display_df['chunk_text'].str[:200] + '...'
                st.dataframe(display_df, use_container_width=True, height=400)
        else:
            st.info("Process documents first to see output preview.")

    # --- Tab 3: Eval Samples ---
    with tab_eval:
        st.subheader("RAG Evaluation Samples")
        st.markdown("Generate synthetic QA pairs from processed chunks for retrieval quality testing.")
        if st.session_state.chunks:
            n_samples = st.slider("Number of samples", 5, 100, 20)
            if st.button("Generate Eval Samples"):
                samples = generate_eval_samples(st.session_state.chunks, max_samples=n_samples)
                st.info(f"Generated {len(samples)} evaluation samples")
                if samples:
                    st.dataframe(pd.DataFrame(samples), use_container_width=True)
                    eval_dir = PROJECT_ROOT / "streamlit_output"
                    eval_path = str(eval_dir / "eval_samples.csv")
                    export_eval_samples(samples, eval_path)
                    with open(eval_path, 'rb') as f:
                        st.download_button("Download eval_samples.csv", f.read(), "eval_samples.csv", mime="text/csv")
        else:
            st.info("Process documents first to generate eval samples.")

    # --- Tab 4: History ---
    with tab_history:
        st.subheader("Processing History")
        if st.session_state.processing_complete and st.session_state.processed_files:
            for p in st.session_state.processed_files:
                (st.success if p['success'] else st.error)(p['message'])
            output_dir, images_dir = create_output_directories()
            _show_download_buttons(output_dir, images_dir, context="history")
            if st.button("Clear History"):
                for key in ['processed_files', 'processing_complete', 'chunks', 'all_table_count', 'all_image_count']:
                    st.session_state[key] = [] if key in ('processed_files', 'chunks') else (False if key == 'processing_complete' else 0)
                st.rerun()
        else:
            st.info("No processing history yet.")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#666;padding:0.5rem'>"
        "RAG Data Preparation Toolkit v3.0"
        "</div>",
        unsafe_allow_html=True,
    )


def _show_download_buttons(output_dir: Path, images_dir: Path, context: str = "main"):
    """Show download buttons for all available export files."""
    for ext, label, mime in [
        ("*.csv", "CSV", "text/csv"),
        ("*.jsonl", "JSONL", "application/json"),
    ]:
        files = sorted(output_dir.glob(ext))
        for f in files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"{label}: {f.name} ({f.stat().st_size / 1024:.1f} KB)")
            with col2:
                with open(f, 'rb') as fh:
                    st.download_button("Download", fh.read(), f.name, mime=mime, key=f"dl_{context}_{f.name}")

    # Images ZIP
    if images_dir.exists():
        image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
        if image_files:
            import io
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for img in sorted(image_files):
                    zf.write(img, img.name)
            zip_buffer.seek(0)
            st.download_button(
                f"Download Extracted Images ({len(image_files)} files, ZIP)",
                zip_buffer.getvalue(),
                "extracted_images.zip",
                mime="application/zip",
                key=f"dl_{context}_images_zip",
            )


if __name__ == "__main__":
    main()
