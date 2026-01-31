# ... (inside tab2 logic) ...

            if len(report) == 0:
                st.success("✅ PASSED. File matches ICE Standard.")
            else:
                st.error(f"❌ FAILED. Found {len(report)} issues.")
                
                # PERFORMANCE FIX: Only show first 100 errors to prevent app freeze
                MAX_DISPLAY = 100
                if len(report) > MAX_DISPLAY:
                    st.warning(f"⚠️ Displaying first {MAX_DISPLAY} errors only (to prevent browser freeze).")
                    df_report = pd.DataFrame(report[:MAX_DISPLAY])
                else:
                    df_report = pd.DataFrame(report)
                
                # Apply styling
                def highlight_row(row):
                    if row.level == 'CRITICAL': return ['background-color: #ffcccc']*len(row)
                    if row.level == 'ERROR': return ['background-color: #ffeeba']*len(row)
                    return ['']*len(row)

                st.table(df_report.style.apply(highlight_row, axis=1))
