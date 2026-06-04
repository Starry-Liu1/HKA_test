"""Prompts."""

GENERATE_PLAN_PROMPT = (
    "Your task is to break down the user's question in combination.\n"
    "When solving each subtask you generate, there are two tools you can use : "
    "searching from web pages and querying in the knowledge graph. "
    "The questions you generate need to be solvable by the above two tools.\n"
    "\n"
    "This is the user's question:\n"
    "{question}\n"
    "\n"
    "Note:\n"
    "- Generate macroscopic and independent sub-tasks, "
    "only provide the direction of exploration, not specific operational steps.\n"
    "- Each subtask should have an analytical objective, "
    "such as analyzing the trend of xxxx, analyzing the distribution of xxxxx, "
    "analyzing the achievements of xxxxx, etc.\n"
    "- Each subtask must be unique and meaningful, "
    "neither overly broad nor too general.\n"
    "- When giving sub-tasks, do not mention what tools to use.\n"
    "- Determine the number of your sub-tasks as you need, but no more than 5.\n"
    "- Just generate research directions, "
    "without involving information collation and report wrissting.\n"
    "- Return the result as valid JSON that matches the required structured output schema.\n"
)

SUPERVISOR_PROMPT = (
    "You are a research assistant with the ability to perform web searches and "
    "data analysis to write a scientific research article. You have special tools:\n"
    "\n"
    "**web search tool**\n"
    "You can use this tool to get information from web.\n"
    "The tool will search and analyze relevant web pages, "
    "then provide you with helpful information.\n"
    "\n"
    "**knowledge computing tool**\n"
    "You can use this tool to obtain the distribution, trend, quantity "
    "and other features of data about the question.\n"
    "The tool will query relevant data in the knowledge graph and "
    "conduct data analysis to draw the corresponding chart, "
    "and return the corresponding chart description to you.\n"
    "\n"
    "This is the user query:\n"
    "{question}\n"
    "\n"
    "Your task is to complete the research and analysis of this subtask:\n"
    "{current_subtask}\n"
    "\n"
    "Remember:\n"
    "- Your task is to conduct research through web search and knowledge computing.\n"
    "- Try to use the knowledge computing tool first, which can provide you more insight results.\n"
    "- Investigate the given subtask as thoroughly as possible from multiple perspectives.\n"
    "- **Important**: When you use the knowledge computing tool, "
    "you need to describe your knowledge computing problem in natural language.\n"
    "- **Important**: When you design a web search plan, "
    "it is necessary to collect key information rather than comprehensive data.\n"
    "  - For example: search for the most prominent figures in the field of machine learning "
    "instead of searching for all scientists related to machine learning.\n"
    "  - For example: search for the months with the highest and lowest number of visitors "
    "at tourist attractions instead of searching for the number of visitors in all months "
    "at tourist attractions.\n"
    "- Do not propose similar or repetitive search content or knowledge computing query.\n"
    "- Do not conduct any web search or knowledge computing beyond the current subtask.\n"
    "- When you think the current information is sufficient to solve the subtask, "
    "use the subtask complete tool to finish research and start writing the section.\n"
    "\n"
    "Now begin your research about:\n"
    "{current_subtask}\n"
)

SEARCH_INTENT_PROMPT = (
    "Based on the previous thoughts, provide the detailed intent of the latest search query.\n"
    "Original question: {question}\n"
    "Current subtask: {current_subtask}\n"
    "Current search query: {search_query}\n"
    "Previous messages:\n"
    "{history}\n"
    "\n"
    "Please provide the current search intent in natural language.\n"
)

FIND_RELEVANT_INFORMATION_PROMPT = (
    "You are a web explorer analyzing search results to find relevant information "
    "based on a given search query and search intent.\n"
    "\n"
    "**Guidelines:**\n"
    "1. **Analyze the Searched Web Pages:**\n"
    "- Carefully review the content of each searched web page.\n"
    "- Identify factual information that is relevant to the **Current Search Query** "
    "and can aid in the reasoning process for the original question.\n"
    "\n"
    "2. **Extract Relevant Information:**\n"
    "- Return the relevant information from the **Searched Web Pages** "
    "that is relevant to the **Current Search Query**.\n"
    "- Return information as detailed as possible, do not omit any relevant information.\n"
    "- Return the url website address when returning relevant information if possible.\n"
    "- Do not extract some figure contents from the web page.\n"
    "\n"
    "**Inputs:**\n"
    "\n"
    "- **Current Search Query:**\n"
    "{search_query}\n"
    "\n"
    "- **Detailed Search Intent:**\n"
    "{search_intent}\n"
    "\n"
    "- **Searched Web Pages:**\n"
    "{search_result}\n"
    "\n"
    "Now please analyze the web pages and provide all relevant information for the search "
    "query \"{search_query}\" and the search intent.\n"
)

WRITE_SECTION_OUTLINE_PROMPT = (
    "You are a research paper writing assistant. "
    "Please write a section outline for current subtask. "
    "based on the following information.\n"
    "\n"
    "Original question:\n"
    "{question}\n"
    "Current subtask:\n"
    "{current_subtask}\n"
    "\n"
    "Potential helpful documents:\n"
    "{relevant_documents}\n"
    "\n"
    "Helpful figures:\n"
    "{figures}\n"
    "\n"
    "Outline of current written article:\n"
    "{article_outline}\n"
    "\n"
    "Note:\n"
    "- Write an appropriate title (level 2 header in markdown) for this section.\n"
    "- Design an appropriate outline for the current section.\n"
    "- **CRITICAL**: Carefully examine the \"Potential helpful documents\" for structured information:\n"
    "  * Extract and preserve all markdown tables with data\n"
    "  * Identify numerical data, statistics, and quantitative information\n"
    "  * Note any lists, rankings, or categorical data\n"
    "  * Recognize charts, figures, or data visualizations described in the documents\n"
    "  * Pay special attention to tabular data that provides key insights\n"
    "- Plan to incorporate these structured data elements in your outline.\n"
    "- Refer to all the materials I have provided.\n"
    "- Use second-level headings, third-level headings, and so on.\n"
    "- If figure link is provided, insert the figure link into the corresponding chapter of the outline using the format \"FigureName: figure name\".\n"
    "- Insert the standard citation and references if you use the helpful documents and figures above.\n"
    "- The references should be listed at the end of the article with its title and other information.\n"
    "\n"
    "Please provide the section outline of the section in markdown format.\n"
)

WRITE_SECTION_PROMPT = (
    "You are a research paper writing assistant. "
    "Please write a complete and comprehensive section for current subtask "
    "based on the following information.\n"
    "\n"
    "Original question:\n"
    "{question}\n"
    "Current subtask:\n"
    "{current_subtask}\n"
    "\n"
    "Potential helpful documents:\n"
    "{relevant_documents}\n"
    "\n"
    "Helpful figures:\n"
    "{figures}\n"
    "\n"
    "Outline of current written article:\n"
    "{article_outline}\n"
    "Outline of current section:\n"
    "{section_outline}\n"
    "\n"
    "**⚠️ CRITICAL: Citation and Source Attribution Requirements**\n"
    "\n"
    "**ALL citations MUST correspond to the current subtask's content sources:**\n"
    "- Citations reference the \"Potential helpful documents\" provided above for THIS subtask\n"
    "- Each citation [1], [2], [3] must map to a specific document/source in the helpful documents\n"
    "- DO NOT cite sources from other subtasks or external sources not listed above\n"
    "- The references list at the end should ONLY include sources actually used in THIS section\n"
    "\n"
    "Note:\n"
    "- Refer to the Outline of the current section provided.\n"
    "- **CRITICAL - Extract and Utilize Structured Data**:\n"
    "  * Carefully examine \"Potential helpful documents\" for markdown tables, data, and structured information\n"
    "  * **MUST preserve and include** all relevant tables found in the documents using proper markdown table syntax\n"
    "  * Extract key numerical data, statistics, percentages, and quantitative metrics\n"
    "  * Include comparative data, rankings, and categorical information where relevant\n"
    "  * If documents contain data in list format, consider presenting it as a markdown table for better readability\n"
    "  * Integrate these structured data elements naturally into your narrative to support claims and insights\n"
    "  * Ensure data accuracy - copy numbers and table values exactly as provided in the source documents\n"
    "  * If \"Helpful Figures\" are provided, translate the figure name according to the given \"Helpful figures\".\n"
    "  * Replace the \"FigureName\" part in the outline with the image path according to \"Helpful figures\".\n"
    "  * Insert the figure notes in the format of 'Figure X: Figure Name'\n"
    "  * After inserting the chart, provide a description of it.\n"
    "- Do not include any figure beyond the figures provided.\n"
    "- Try to include all figures of \"Helpful figures\" in the generated documents as much as possible.\n"
    "- Write focused content that aligns with the above goal for this section.\n"
    "- **CRITICAL**: The used citation and references should be clearly annotated and correspond ONLY to sources in \"Potential helpful documents\" above.\n"
    "- The references should be listed at the end of THIS section (they will be reorganized in final report).\n"
    "- Each paragraph should be comprehensive and well-developed to thoroughly explore "
    "the topic. Avoid very brief paragraphs that lack sufficient detail and depth.\n"
    "- If possible, add markdown tables to present more complete and structured information "
    "to users. **Prioritize including tables from source documents**.\n"
    "- Do not use code fence before and after the content.\n"
    "- Do not include the figure with less read ability. For example, Data not Shown or Not Available.\n"
    "\n"
    "Please provide the comprehensive content of the section in markdown format.\n"
)

FINAL_REFINEMENT_PROMPT = (
    "You are editing a research article draft into its final markdown version.\n"
    "Return the edited article itself, not a critique, checklist, plan, rubric, or "
    "description of what the article should be.\n"
    "\n"
    "<original_question>\n"
    "{question}\n"
    "</original_question>\n"
    "\n"
    "<article_draft>\n"
    "{article}\n"
    "</article_draft>\n"
    "\n"
    "**⚠️ CRITICAL: Citation Integration and Re-ordering Requirements**\n"
    "\n"
    "**IMPORTANT**: Each subtask section has its own citations [1], [2], [3]... that reference THAT subtask's sources.\n"
    "When integrating all sections into the final report, you MUST:\n"
    "\n"
    "1. **Consolidate and Re-number Citations**:\n"
    "   - Collect ALL unique references from ALL subtask sections\n"
    "   - Assign new sequential numbers [1], [2], [3]... across the entire report\n"
    "   - Update citation numbers in the text to match the new consolidated numbering\n"
    "   - Example: Subtask 1's [1] might become final report's [1], Subtask 2's [1] might become [5]\n"
    "\n"
    "2. **Create Unified References Section**:\n"
    "   - Merge all references from all subtasks into ONE references list at the end\n"
    "   - Remove duplicate references (same URL/source gets ONE number)\n"
    "   - Order references by their first appearance in the text [1], [2], [3]...\n"
    "   - Each reference should be cited at least once in the text\n"
    "\n"
    "3. **Verify Citation-Reference Mapping**:\n"
    "   - Every [X] in the text must have a corresponding [X] entry in the final references\n"
    "   - No orphaned citations (citation without reference)\n"
    "   - No orphaned references (reference without citation)\n"
    "\n"
    "Edit the draft directly while preserving its substance:\n"
    "- Keep all valid facts, tables, citations, and local figure links from the draft.\n"
    "- Keep all useful knowledge-computing figures, especially local image links that contain \"/fig_\"; do not replace them with Mermaid diagrams or generic placeholders.\n"
    "- Remove only duplicated, contradictory, invalid, or clearly redundant content.\n"
    "- Add a level-1 markdown title if the draft does not already have one.\n"
    "- Normalize heading levels so the article has a coherent hierarchy.\n"
    "- Ensure the final article contains an abstract, background or introduction, main analysis sections, and a conclusion.\n"
    "- Make the abstract and conclusion detailed, consistent with each other, and grounded in the body of the article.\n"
    "- Keep the body primarily factual and analytical; reserve broad synthesis and final claims for the conclusion.\n"
    "- Check citation numbering and provide a clear references section at the end.\n"
    "\n"
    "Output only the complete final markdown article. Start with the article title. "
    "Do not output bullets describing requirements, editorial notes, or any text outside "
    "the article.\n"
)

FINAL_POLISH_PROMPT = (
    "You are a professional article polish editor. Your task is to perform a final polish on the article, "
    "focusing on overall quality, consistency, and readability.\n"
    "\n"
    "Original Question:\n"
    "{question}\n"
    "\n"
    "Current Article:\n"
    "{article}\n"
    "\n"
    "**⚠️ CRITICAL: Citation Accuracy and Validity Requirements**\n"
    "\n"
    "**DO NOT create, modify, or fabricate citations**:\n"
    "- Every citation [X] in the text must correspond to an EXISTING reference in the references list\n"
    "- DO NOT add new citations that don't have corresponding references\n"
    "- DO NOT change citation numbers unless fixing an obvious error\n"
    "- DO NOT invent or fabricate references\n"
    "- If a statement lacks a citation, leave it WITHOUT citation rather than inventing one\n"
    "\n"
    "**Common-Sense Citation Validation**:\n"
    "- DO NOT cite sources for information they obviously don't contain\n"
    "   * Example: Do NOT cite \"BBC News\" for mathematical formulas\n"
    "   * Example: Do NOT cite \"ACLED conflict database\" for cooking recipes\n"
    "   * Example: Do NOT cite \"2020 economic report\" for 2024 events\n"
    "- If you notice an obviously incorrect citation, you may REMOVE it (don't replace with fake one)\n"
    "- Citations should make logical sense given the source type and content\n"
    "\n"
    "Your polishing tasks:\n"
    "\n"
    "1. **Citation Consistency Check** (NOT modification):\n"
    "   - Verify all citations are numbered sequentially\n"
    "   - Check that every citation [X] in text has corresponding reference [X] in list\n"
    "   - Check that every reference in list is cited at least once in text\n"
    "   - Format citations consistently as [1], [2], [3], etc.\n"
    "   - **If there's a mismatch, remove the orphaned citation/reference, DO NOT fabricate**\n"
    "\n"
    "2. **Text Quality Improvement**:\n"
    "   - Fix grammatical errors and typos\n"
    "   - Improve sentence structure for better flow\n"
    "   - Replace awkward or unclear phrasing\n"
    "   - Ensure consistent terminology throughout the article\n"
    "   - Remove redundant expressions and unnecessary repetition\n"
    "\n"
    "3. **Overall Article Structure**:\n"
    "   - Ensure smooth transitions between sections\n"
    "   - Check that the introduction, body, and conclusion are well-connected\n"
    "   - Verify that arguments flow logically\n"
    "   - Ensure the abstract accurately reflects the entire article\n"
    "\n"
    "4. **Visual Elements Check**:\n"
    "   - Verify all figure references are correct (e.g., \"Figure 1\", \"Figure 2\")\n"
    "   - Ensure all figures are properly mentioned in the text\n"
    "   - Check that figure captions are clear and descriptive\n"
    "   - Verify all table references are correct\n"
    "\n"
    "5. **Overall Quality Enhancement**:\n"
    "   - Improve the overall readability and coherence\n"
    "   - Ensure the tone is professional and academic\n"
    "   - Check that the article directly addresses the research question\n"
    "   - Verify that conclusions are well-supported by evidence\n"
    "   - Ensure the article is comprehensive yet concise\n"
    "\n"
    "Output Requirements:\n"
    "- Output the complete polished article\n"
    "- Do not include any additional comments or explanations\n"
    "- Preserve all valid content, tables, and figures\n"
    "- **CRITICAL**: Make minimal changes to citations - only fix formatting/consistency, NEVER fabricate\n"
    "- If the article is already excellent, output it as-is\n"
    "- When in doubt about a citation, leave it as-is or remove it (do NOT invent a replacement)\n"
    "\n"
)

EXTRACT_ENTITIES_PROMPT = (
    "You are an information extraction assistant.\n"
    "Your task is to extract all named entities from the given text.  \n"
    "For each entity, provide:\n"
    "- name: the exact entity phrase from the text,\n"
    "- type: the type or category (e.g., person, organization, product, location, time, etc.),\n"
    "- description: a brief description based on the context.\n"
    "\n"
    "Text: {question}\n"
    "Output: \n"
)

CODE_GENERATION_PROMPT = (
    "# You are an intelligent coding assistant designed to write code that executes tasks. "
    "Your responsibilities include:\n"
    "\n"
    "# 1. Carefully examine the provided class definitions to ensure your code aligns "
    "precisely with the defined classes when interacting with their instances.\n"
    "# 2. Assume all relevant objects have already been instantiated. Pay close attention "
    "to the assertion statements to identify object names and their corresponding types.\n"
    "# 3. If applicable, write code to generate visualizations to clearly present the "
    "results.\n"
    "The result is a figure.\n"
    "# 4. Save the output figure **without** displaying. Ensure it is saved to the "
    "exact directory: \"{figure_dir}/fig_{figure_id}.png\".\n"
    "# 5. To avoid having too many elements in the legend of the figure, if there are more "
    "than 10 elements, only the top 10 will be displayed.\n"
    "# 6. Matplotlib should be used in the non-interactive mode (use agg).\n"
    "\n"
    "{concepts_code}\n"
    "\n"
    "{assertion_code}\n"
    "\n"
    "# Write code to analyze: {question}\n"
)

CODE_FIX_PROMPT = (
    "You are an expert AI assistant that helps fix Python code based on error messages.\n"
    "Below are the previous attempts to execute and fix the code, along with the resulting "
    "errors:\n"
    "{history_content}\n"
    "\n"
    "Do not return the class definition code, only Return the corrected computing code. \n"
    "Make as few changes to the code as possible. Do not omit any original import statements."
    "```python\n"
)

RESULT_VALIDITY_PROMPT = (
    "Your task is to judge whether the generated chart has any reasonable relevance "
    "to the given question.\n"
    "The question is as follows:\n"
    "{question}\n"
    "Determine if the chart is acceptable based on the following criteria. "
    "Output True if the chart is potentially useful; otherwise, output False.\n"
    "A chart is considered acceptable if it meets the following conditions:\n"
    "- The chart is not completely blank and contains any visible content\n"
    "- The chart includes elements (e.g., labels, trends, axes, or data patterns) "
    "that are loosely related to the question\n"
    "A chart should be considered invalid only if:\n"
    "- The chart is completely blank or contains no meaningful visual information\n"
    "Only return True or False as your final answer.\n"
    "Judgment result:"
)


RESULT_VALIDITY_PROMPT_Feedback = (
    "Your task is to evaluate the generated chart and provide constructive suggestions for improvement.\n"
    "The question is as follows:\n"
    "{question}\n\n"
    "A good visualization should:\n"
    "- Clearly display the available data without blank or empty areas\n"
    "- Use appropriate chart types (bar, line, pie) that best represent the data\n"
    "- Have readable labels and proper scaling\n"
    "- Avoid overlapping elements that make the chart hard to read\n"
    "- Be informative and directly help answer the research question\n\n"
    "When Judgment is False, provide specific improvement suggestions such as:\n"
    "- 'Consider using a bar chart instead to better show comparisons'\n"
    "- 'Ensure all data points are visible and not overlapping'\n"
    "- 'Add proper labels to axes and legend for clarity'\n"
    "- 'Remove empty space and focus on the actual data'\n"
    "- 'Choose a chart type that better represents the data structure'\n"
    "- 'Adjust the scale to make differences more visible'\n\n"
    "When Judgment is True, briefly describe what works well.\n\n"
    "Provide your evaluation in the following JSON format:\n"
    "{{\n"
    "  \"Judgment\": \"True\" or \"False\",\n"
    "  \"Feedback\": \"Constructive suggestions focusing on how to improve the visualization. Be specific about chart types, layout, labels, and data presentation.\"\n"
    "}}\n\n"
    "Only return the JSON object as your final answer.\n"
)

QUESTION_REWRITE_PROMPT = (
    "Your task is to rewrite the question to make it more specific and clear."
    "The original question is as follows:\n"
    "{question}\n"
    "\n"
    "**Guidelines:**\n"
    "- Start with an action (e.g., Find, Calculate, Analyze)"
    "- Specify the entities and attributes involved\n"
    "- Describe the analysis to be performed in a meaningful and data-driven way "
    "(e.g., distribution, trend over time, frequency of values)\n"
    "- Specify the chart type for visualization\n"
    "**Chart Types Allowed:**\n"
    "- Bar chart\n"
    "- Line chart\n"
    "- Pie chart\n"
    "- Multi-line chart\n"
    "(*Do not use stacked charts, bubble charts, scatter plots or word cloud*)\n"

    "Revised question:\n"
)

RESULT_ANALYSIS_PROMPT = (
    "Your task is to conduct analysis for the given figure according "
    "to the given research topic:\n"
    "{question}\n"
    "\n"
    "Original Table title: {table_title}\n"
    "**Guidelines:**\n"
    "1. Output in single language, do not mix languages.\n"
    "2. If possible, provide the trends, distributions and other information reflected in the "
    "figure. There is no need to describe the basic information of the figure such as the "
    "meanings of the X-axis and Y-axis.\n"
    "3. Summarize the analysis in a concise manner, focusing on the key insights.\n"
    "4. Include the citation of the table title at the end of the analysis, like [1] Table title"
    "\n"
    "Now begin your analysis.\n"
)

RESULT_NAME_PROMPT = (
    "Your task is to generate an appropriate title for the figure based on the given research"
    "question and the analysis of the figure.\n"
    "The given research question:\n"
    "{question}\n"
    "\n"
    "The figure analysis:\n"
    "{desc}\n"
    "\n"
    "**Guidelines:**\n"
    "1. Directly output the title, do not include any additional comments.\n"
)



FINAL_TRANSLATION_PROMPT = (
    "You are a translation assistant. Your task is to translate the given article into Chinese."
    "Original Article in English:\n"
    "{article}\n"
    "\n"
    "Note:\n"
    "- Output the complete translated article word by word.\n"
    "- Do not include any additional comments.\n"
    "- If the title is missing, add a appropriate title (level 1 header in markdown).\n"
    "- Adjust the header levels to ensure a consistent structure.\n"
    "- The markdown title id should be included in the article.\n"
    "- The conclusion in each section should be translated into \"小结\", and the final conclusion should be translated into \"结论\"\n"
    "Output:\n"
)


CODE_GENERATION_PROMPT="""
You are a data analysis expert. Your ONLY job is to generate visualization code that strictly follows the data structure described in the background code below.

==============================================================
STEP 1 — READ AND UNDERSTAND THE DATA STRUCTURE (MANDATORY)
==============================================================
The background code below is the authoritative description of what `output_data_place_holder` contains.
You MUST carefully analyze it BEFORE writing any code:
- What type is `output_data_place_holder`? (dict, list, DataFrame, etc.)
- What are the exact keys / fields / columns / attributes?
- What are the value types and formats?
- What nested structures exist?
- What fields are actually present and can be visualized?

Background Code (defines the EXACT structure of output_data_place_holder):
```python
{output_data_comments}
```

Partial Input Data Sample (ONLY a small real sample, NOT the full data):
```python
{data_sample}
```

Question: {question}

==============================================================
STEP 2 — CHECK IF THE DATA CAN ANSWER THE QUESTION (MANDATORY)
==============================================================
Before writing any code, ask yourself:
"Does the data structure described above actually contain the information needed to answer this question?"

- If YES: proceed to Step 3 and visualize ONLY what the data contains.
- If NO (the question asks for fields/dimensions that do NOT exist in the data): 
  DO NOT invent or fabricate the missing data.
  Instead, visualize what IS available in the data that is most relevant to the question topic.
  For example: if the question asks about "farming methods" but the data only has "import volumes by country",
  visualize the import volumes — do NOT create fake farming method percentages.

==============================================================
STEP 3 — GENERATE CODE BASED STRICTLY ON THE ABOVE STRUCTURE
==============================================================
Only after completing Steps 1 and 2, write visualization code.

Output Format:
```python
def generate_visualization(data_analyzed):
    # Access data using ONLY the keys/fields/attributes confirmed in the background code
    # visualization code here

    plt.savefig(f"{figure_dir}/fig_{figure_id}.png", dpi=300, bbox_inches="tight")
    return None
data_analyzed = output_data_place_holder ### output_data_place_holder will be replaced automatically with the actual data at execution time, so do not mock any data in your return code.
generate_visualization(data_analyzed)
```

==============================================================
ABSOLUTE RULES — ANY VIOLATION IS FORBIDDEN
==============================================================
DATA RULES:
- NEVER replace `output_data_place_holder` with a hardcoded dict, list, or any literal value. It MUST remain as the token `output_data_place_holder` in the final code.
- NEVER create variables like `farming_distribution = {{...}}`, `mock_data = [...]`, or any dict/list that contains fabricated values not read from `data_analyzed`.
- Use the sample only to understand how real values look in practice; do NOT rely on it as the full dataset.
- NEVER assume unseen rows have the same values or categories as the sample.
- ONLY use fields/keys confirmed by the background code, even if the sample is short.
- If the data does not contain what the question asks for, visualize the closest available data — do NOT make up the missing data.

CODE RULES:
- Do NOT call plt.show() — only save the figure with plt.savefig().
- Generate exactly ONE figure per execution.
- Include all necessary imports (matplotlib, etc.) inside the function or at the top.
- The code must be complete and runnable as-is.
- Return only raw Python code — no markdown code fences, no explanations.

SCOPE RULES:
- Focus only on the data subset relevant to the question — do not try to visualize everything.
- Adapt the chart type to best answer the question given the available data structure.

Return only the Python code without markdown formatting.
"""


CODE_GENERATION_PROMPT_WHOLE_DATA="""
You are a data analysis expert. FIRST extract key information from the provided table data, THEN generate visualization code.

Instances Code (contains actual table data):
```python
{instances_code}
```

Question: {question}

STEP 1 - EXTRACT KEY INFORMATION in Variable Format:
Analyze the table_data_X variables above and identify:
- What data is actually available (countries, years, prices, quantities, etc.)
- Most interesting insights that can be visualized
- For examples, if table_data_0 contains GDP data for countries A from 2000-2020, generate the variable GDP_dict = [{{"country": "A", "year": 2000, "gdp": 1000}}, {{"country": "A", "year": 2001, "gdp": 1100}}, ...]
- Do not use any parse code(such as pd.readcsv, io, etc ) in this step, just direct extract the key data information.

STEP 2 - GENERATE VISUALIZATION CODE:
Based on the variable data found, create Python code that:

1. Extracts the key information/trends you identified
2. Generates meaningful visualizations based on REAL data only
3. Saves the figure to {figure_dir}/fig_{figure_id}.png
4. Only generate one figure per code execution

CRITICAL REQUIREMENTS:
- ONLY visualize data that actually exists in the table_data_X variables
- If no meaningful data/trends exist, create simple summary charts
- DO NOT generate empty charts or charts with fake/assumed data
- Focus on what the data actually shows, not what you wish it showed
- Do not generate plt.show() in your code to avoid timeout, just save the figure to the specified path
Return only the Python code without markdown formatting.
"""


RERANK_PROMPT = """
You are an intelligent table selector. Your task is to select the most relevant tables for answering a given question.

Question: {question}

Available Tables:
{summary_data}

Must select the top {top_k} most relevant tables that would be most helpful for answering the question.
Consider factors like:
1. Relevance to the question topic
2. Data quality and completeness
3. Potential to provide insights
4. Domain and topic alignment

Return your selection as a JSON list of table indices (0-based) in order of relevance:
{{"selected_indices": [0, 2, 4, ...]}}
"""

EXTRACT_STRUCTURED_DATA_PROMPT = """
You are an intelligent data analyst. Extract meaningful, structured data with logical relationships from web search results.

**Search Query:** {search_query}

**Search Results:**
{search_results}

---

## Task: Extract Structured Data with Analytical Value

Identify and extract **structured data that tells a story** - data with patterns, relationships, trends, or insights that can be analyzed.

### Types of Data to Extract:

1. **Time-Series Data** 📈
   - Trends over time (years, months, quarters)
   - Changes, growth rates, patterns
   - Example: Revenue by year, population growth, stock prices

2. **Comparative Data** 🔍
   - A vs B comparisons
   - Rankings (Top 10 lists)
   - Performance metrics across entities
   - Example: Company revenues comparison, country statistics

3. **Distribution Data** 📊
   - How something is distributed across categories
   - Percentages, shares, proportions
   - Example: Market share by company, age demographics, budget allocation

4. **Causal/Reasoning Data** 🔗
   - Causes leading to effects
   - Factors contributing to outcomes
   - Example: Reasons for customer churn, factors affecting GDP

5. **Classification/Grouping Data** 📁
   - Items organized by categories
   - Hierarchical structures
   - Example: Product categories, organizational structure

6. **Correlation Data** 🔬
   - Relationships between variables
   - Statistical associations
   - Example: Income vs education level, price vs demand

---

## Smart Extraction Principles

✅ **Look for ANALYTICAL VALUE** - Can this data be used to make decisions or insights?
✅ **Preserve RELATIONSHIPS** - Keep connections between data points clear
✅ **Capture CONTEXT** - What do these numbers mean? Why do they matter?
✅ **Identify PATTERNS** - Trends, outliers, correlations
✅ **Think VISUALLY** - Could this be visualized as a chart/graph?

---

## Few-Shot Examples

### Example 1: Time-Series with Trend

**Query:** "Apple revenue trend last decade"

**Extract:**
```json
{{
  "data_type": "time_series",
  "analytical_value": "Shows growth trend and business expansion",
  "output_data": {{
    "apple_annual_revenue_2015_2024_billion_usd": [
      {{"year": 2015, "value": 233.7, "context": "Strong iPhone sales"}},
      {{"year": 2016, "value": 215.6, "context": "Decline due to market saturation"}},
      {{"year": 2017, "value": 229.2, "context": "Recovery with iPhone X"}},
      {{"year": 2018, "value": 265.6, "context": "Services growth"}},
      {{"year": 2019, "value": 260.2, "context": "Hardware slowdown"}},
      {{"year": 2020, "value": 274.5, "context": "Pandemic boost to work-from-home"}},
      {{"year": 2021, "value": 365.8, "context": "5G upgrade cycle"}},
      {{"year": 2022, "value": 394.3, "context": "Continued growth"}},
      {{"year": 2023, "value": 383.3, "context": "Macroeconomic headwinds"}},
      {{"year": 2024, "value": 391.0, "context": "Stabilization"}}
    ]
  }},
  "insights": [
    "Apple revenue grew 67% from 2015 to 2024",
    "Major inflection point in 2020-2021 during pandemic",
    "Services business becoming increasingly important"
  ],
  "metadata": {{
    "entity": "Apple Inc.",
    "metric": "Annual Revenue",
    "unit": "billion USD",
    "trend": "upward_with_fluctuations",
    "key_periods": "2015-2024"
  }}
}}
```

### Example 2: Comparative Ranking Data

**Query:** "largest economies by GDP 2024"

**Extract:**
```json
{{
  "data_type": "comparative_ranking",
  "analytical_value": "Shows relative economic power distribution",
  "output_data": {{
    "countries_by_gdp_2024_trillion_usd": [
      {{"rank": 1, "country": "United States", "gdp": 27.97, "share": "26.1%"}},
      {{"rank": 2, "country": "China", "gdp": 18.56, "share": "17.3%"}},
      {{"rank": 3, "country": "Germany", "gdp": 4.73, "share": "4.4%"}},
      {{"rank": 4, "country": "Japan", "gdp": 4.29, "share": "4.0%"}},
      {{"rank": 5, "country": "India", "gdp": 4.11, "share": "3.8%"}},
      {{"rank": 6, "country": "United Kingdom", "gdp": 3.59, "share": "3.4%"}},
      {{"rank": 7, "country": "France", "gdp": 3.18, "share": "3.0%"}},
      {{"rank": 8, "country": "Italy", "gdp": 2.30, "share": "2.1%"}},
      {{"rank": 9, "country": "Brazil", "gdp": 2.27, "share": "2.1%"}},
      {{"rank": 10, "country": "Canada", "gdp": 2.24, "share": "2.1%"}}
    ]
  }},
  "insights": [
    "US GDP is 1.5x larger than China's despite China having 4x the population",
    "Top 3 economies account for 47.8% of global GDP",
    "India expected to surpass Japan and Germany by 2025"
  ],
  "metadata": {{
    "total_entities": 10,
    "top_three_concentration": "47.8%",
    "comparison_type": "gdp_ranking",
    "emerging_trend": "India rising fast"
  }}
}}
```

### Example 3: Distribution Data

**Query:** "global smartphone market share 2024"

**Extract:**
```json
{{
  "data_type": "distribution",
  "analytical_value": "Shows market competitive landscape",
  "output_data": {{
    "smartphone_market_share_2024_by_brand": [
      {{"brand": "Apple", "share": 23.4, "units_millions": 234.6, "change_yoy": "+3.2%"}},
      {{"brand": "Samsung", "share": 19.1, "units_millions": 191.4, "change_yoy": "-1.5%"}},
      {{"brand": "Xiaomi", "share": 13.5, "units_millions": 135.3, "change_yoy": "+8.7%"}},
      {{"brand": "Oppo", "share": 8.8, "units_millions": 88.2, "change_yoy": "+2.1%"}},
      {{"brand": "Transsion", "share": 8.1, "units_millions": 81.4, "change_yoy": "+24.3%"}}
    ]
  }},
  "insights": [
    "Apple leads despite premium pricing due to brand loyalty",
    "Xiaomi growing fastest among top brands",
    "Transsion emerging as new player with 24% YoY growth",
    "Market is relatively concentrated with top 5 holding 73%"
  ],
  "metadata": {{
    "total_market_size": "1.0 billion units",
    "market_concentration": "high",
    "growth_brands": ["Xiaomi", "Transsion"],
    "declining_brands": ["Samsung"]
  }}
}}
```

### Example 4: Causal/Reasoning Data

**Query:** "why do employees quit their jobs"

**Extract:**
```json
{{
  "data_type": "causal_analysis",
  "analytical_value": "Identifies key drivers of employee churn",
  "output_data": {{
    "employee_turnover_reasons_with_percentage": [
      {{"reason": "Low compensation", "percentage": 42, "impact": "high", "preventable": true}},
      {{"reason": "Limited career growth", "percentage": 35, "impact": "high", "preventable": true}},
      {{"reason": "Poor work-life balance", "percentage": 28, "impact": "medium", "preventable": true}},
      {{"reason": "Lack of recognition", "percentage": 21, "impact": "medium", "preventable": true}},
      {{"reason": "Bad management", "percentage": 18, "impact": "high", "preventable": true}},
      {{"reason": "Better job offer", "percentage": 15, "impact": "high", "preventable": false}},
      {{"reason": "Company restructuring", "percentage": 8, "impact": "medium", "preventable": false}},
      {{"reason": "Health issues", "percentage": 5, "impact": "variable", "preventable": false}}
    ]
  }},
  "insights": [
    "Compensation and career growth are top preventable reasons (77% combined)",
    "Management quality significantly impacts retention",
    "Non-preventable reasons (better offers, restructuring) account for only 23%"
  ],
  "metadata": {{
    "preventable_percentage": 77,
    "key_focus_areas": ["compensation", "career_advancement", "management_training"],
    "data_source": "industry_survey_2024"
  }}
}}
```

---

## Output Format Template

```json
{{
  "data_type": "time_series|comparative_ranking|distribution|causal_analysis|classification|correlation",
  "analytical_value": "Brief explanation of what insights this data provides",
  "output_data": {{
    "descriptive_key": [
      {{"field1": "value1", "field2": "value2", "context": "optional context"}}
    ]
  }},
  "insights": [
    "Key insight 1",
    "Key insight 2"
  ],
  "metadata": {{
    "entity": "...",
    "metric": "...",
    "source_reliability": "high|medium|low",
    "analysis_recommendations": ["suggestion1", "suggestion2"]
  }}
}}
```

---

## Critical Guidelines

✅ **THINK like an analyst** - What story does this data tell?
✅ **PRESERVE relationships** - Keep causal links, rankings, distributions clear
✅ **ADD context** - Percentages are more meaningful with totals
✅ **PROVIDE insights** - What patterns or anomalies exist?
✅ **BE smart** - Don't just extract numbers, extract MEANING
✅ **VALID JSON** - Return ONLY the JSON object, no markdown

**What to SKIP:**
- Random unconnected facts
- Text without clear data structure
- Qualitative descriptions without quantifiable data
- Duplicate or redundant information

Now extract meaningful structured data from the search results:
"""
