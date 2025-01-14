import os
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re
import shutil

class WhiteThemeIntegrator:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.tufte_dir = self.base_dir / 'tufte_tests'
        self.structure = {
            'overview': ['creator.html', 'temporal.html', 'geographic.html'],
            'access': ['instructions.html', 'requirements.html'],
            'standards': ['structure.html'],
            'codebook': ['fields.html'],
            'context': ['analysis.html'],
            'uses': ['applications.html'],
            'sources': ['references.html']
        }
        
    def copy_data_files(self):
        """Copy necessary data files to the same directory as the output HTML."""
        # We don't need to copy files since they're already in the right place
        data_files = [
            'atlanta_walkability_wgs84.geojson',
            'force_graph_data.json',
            'temporal_data.json'
        ]
        
        # Just verify the files exist
        missing_files = []
        for file in data_files:
            if not (self.base_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print("Warning: Missing data files:", missing_files)
    
    def extract_content(self, file_path):
        """Extract content from a Tufte page, preserving scripts and data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove navigation elements
            for nav in soup.find_all(class_=['nav-buttons', 'control-button', 'controls']):
                nav.decompose()
            
            # Extract styles
            styles = []
            for style in soup.find_all('style'):
                if style.string:
                    styles.append(style.string)
            
            # Extract scripts and preserve D3 initialization
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    # Add all necessary D3 dependencies
                    src = script['src']
                    if any(lib in src for lib in ['d3', 'topojson']):
                        scripts.append({'src': src})
                elif script.string:
                    # Fix data file paths in the script
                    js_content = script.string
                    js_content = js_content.replace('../../', '')
                    js_content = js_content.replace('../', '')
                    
                    # Special handling for force graph data
                    if 'forceSimulation' in js_content:
                        if not soup.find(class_='connection-graph'):
                            js_content = js_content.replace(
                                'document.querySelector(\'.connection-graph\')',
                                'document.querySelector(\'.force-graph\')'
                            )
                    
                    # Special handling for temporal chart
                    if 'temporal-chart' in js_content:
                        js_content = js_content.replace(
                            'document.querySelector(\'.chart\')',
                            'document.querySelector(\'.temporal-chart\')'
                        )
                    
                    # Special handling for structure diagram
                    if 'structure-diagram' in js_content:
                        js_content = js_content.replace(
                            'document.querySelector(\'.structure-diagram\')',
                            'document.querySelector(\'.structure-tree\')'
                        )
                    
                    scripts.append({'content': js_content})
            
            # Extract main content and preserve containers
            main_content = soup.find('body')
            if main_content:
                # Remove navigation
                for nav in main_content.find_all('div', class_='navigation'):
                    nav.decompose()
                
                # Keep the original structure for visualization containers
                content = str(main_content).replace('<body>', '').replace('</body>', '').strip()
                
                # Add force graph container if needed
                if any('forceSimulation' in s.get('content', '') for s in scripts):
                    content = content.replace(
                        '<div class="connection-graph"',
                        '<div class="force-graph" style="width: 100%; height: 400px;"'
                    )
                
                # Add temporal chart container if needed
                if any('temporal-chart' in s.get('content', '') for s in scripts):
                    content = content.replace(
                        '<div class="chart"',
                        '<div class="temporal-chart"'
                    )
                
                # Add structure tree container if needed
                if any('structure-diagram' in s.get('content', '') for s in scripts):
                    content = content.replace(
                        '<div class="structure-diagram"',
                        '<div class="structure-tree" style="width: 100%; height: 500px;"'
                    )
                
                # Create a container for the content
                content = f'<div class="tufte-content">{content}</div>'
            
            return {
                'styles': styles,
                'scripts': scripts,
                'content': content
            }
    
    def generate_integrated_html(self):
        """Generate the integrated datawalker HTML with light theme."""
        # First, copy necessary data files
        self.copy_data_files()
        
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Walking Through Data | Atlanta Walkability</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://d3js.org/d3-geo.v3.min.js"></script>
    <script src="https://d3js.org/topojson.v3.min.js"></script>
    <script src="https://unpkg.com/intersection-observer"></script>
    <script src="https://unpkg.com/scrollama"></script>
    <style>
        :root {
            --text: #222;
            --background: #fff;
            --highlight: #1a5f7a;
            --muted: #666;
            --spacing: 2rem;
            --transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            
            /* Tufte-inspired colors */
            --tufte-background: #fffff8;
            --tufte-text: #111;
            --tufte-gray: #666;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: var(--background);
            color: var(--text);
            font-family: "ET Book", Georgia, serif;
            line-height: 1.6;
            overflow-x: hidden;
        }

        /* Progress tracking */
        .data-path {
            position: fixed;
            top: 0;
            left: 0;
            width: 3px;
            height: 100vh;
            background: #eee;
            margin-left: 2rem;
            z-index: 100;
        }

        .data-path::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            background: var(--highlight);
            transition: height 0.5s ease;
        }

        .section {
            min-height: 100vh;
            padding: 2rem 4rem 2rem 6rem;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .node {
            position: absolute;
            left: 2rem;
            width: 0.75rem;
            height: 0.75rem;
            background: #eee;
            border-radius: 50%;
            transform: translateX(-0.375rem);
            transition: var(--transition);
            z-index: 101;
        }

        .node.active {
            background: var(--highlight);
            transform: translateX(-0.375rem) scale(1.2);
        }

        .content {
            max-width: 1200px;
            margin: 0 auto;
            opacity: 0.3;
            transform: translateX(20px);
            transition: var(--transition);
        }

        .section.active .content {
            opacity: 1;
            transform: translateX(0);
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 400;
            margin-bottom: var(--spacing);
            color: var(--text);
        }

        h1 { 
            font-size: 2.5em;
            font-style: italic;
        }

        h2 { 
            font-size: 2em;
            color: var(--highlight);
        }

        p {
            margin-bottom: var(--spacing);
            max-width: 65ch;
            font-size: 1.1em;
            line-height: 1.7;
            color: var(--text);
        }

        /* Visualization containers */
        .tufte-container {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .tufte-content {
            color: var(--tufte-text);
        }

        /* Map specific styles */
        .map-container {
            position: relative;
            height: 600px;
            background: var(--tufte-background);
        }

        .legend {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border: 1px solid #ddd;
            z-index: 1000;
        }

        .legend-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }

        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 10px;
        }

        .legend-label {
            font-size: 0.8em;
        }

        .region-highlight {
            position: absolute;
            padding: 1rem;
            background: var(--tufte-background);
            border-left: 3px solid var(--highlight);
            max-width: 200px;
            font-size: 0.9em;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            z-index: 1000;
        }

        /* Stats container */
        .stats-container {
            padding: 1rem;
            background: var(--tufte-background);
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .stat {
            margin-bottom: 1.5rem;
        }

        .stat-value {
            font-size: 1.2em;
            color: var(--highlight);
            margin: 0.2em 0;
        }

        .stat-label {
            font-size: 0.9em;
            color: var(--tufte-gray);
        }

        /* Progress label */
        .progress-label {
            position: fixed;
            left: 4rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9em;
            color: var(--muted);
            font-style: italic;
            transition: var(--transition);
            pointer-events: none;
            z-index: 102;
        }

        .progress-label.active {
            color: var(--highlight);
        }

        /* Scroll prompt */
        .scroll-prompt {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            color: var(--muted);
            font-size: 0.9em;
            font-style: italic;
            opacity: 0.7;
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            z-index: 102;
        }

        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }

        .scroll-arrow {
            animation: bounce 1.5s infinite;
            color: var(--highlight);
        }

        /* Hide navigation elements */
        .nav-buttons,
        .control-button,
        .controls,
        [class*="nav-"],
        [class*="control-"] {
            display: none !important;
        }

        /* Grid layout for geographic container */
        .geo-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 2rem;
            margin: 2rem 0;
        }

        /* Force Graph Styles */
        .force-graph {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .force-graph svg {
            width: 100%;
            height: 100%;
        }

        .force-graph .node circle {
            fill: var(--highlight);
            stroke: var(--tufte-background);
            stroke-width: 1.5px;
        }

        .force-graph .node text {
            fill: var(--tufte-text);
            font-size: 12px;
            font-family: "ET Book", Georgia, serif;
        }

        .force-graph .link {
            stroke: var(--tufte-gray);
            stroke-opacity: 0.4;
            stroke-width: 1.5px;
        }

        .force-graph .node:hover circle {
            fill: var(--text);
        }

        .force-graph .node:hover text {
            font-weight: bold;
        }

        /* Temporal Chart Styles */
        .temporal-chart {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            height: 400px;
        }

        .temporal-chart svg {
            width: 100%;
            height: 100%;
        }

        .temporal-chart .area {
            fill: var(--highlight);
            fill-opacity: 0.1;
        }

        .temporal-chart .line {
            fill: none;
            stroke: var(--highlight);
            stroke-width: 2px;
        }

        .temporal-chart .annotation text {
            font-family: "ET Book", Georgia, serif;
            font-size: 12px;
            fill: var(--tufte-gray);
        }

        .temporal-chart .axis {
            font-family: "ET Book", Georgia, serif;
            font-size: 12px;
        }

        .temporal-chart .axis line,
        .temporal-chart .axis path {
            stroke: var(--tufte-gray);
        }

        .temporal-chart .axis text {
            fill: var(--tufte-text);
        }

        .temporal-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--spacing);
            margin: var(--spacing) 0;
        }

        .temporal-cell {
            background: var(--tufte-background);
            padding: var(--spacing);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            text-align: center;
        }

        .temporal-value {
            font-size: 1.5em;
            color: var(--highlight);
            margin-bottom: 0.5rem;
        }

        .temporal-label {
            font-size: 0.9em;
            color: var(--tufte-gray);
            font-style: italic;
        }

        /* Structure Tree Styles */
        .structure-tree {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .structure-tree svg {
            width: 100%;
            height: 100%;
        }

        .structure-tree .node circle {
            fill: var(--highlight);
            stroke: var(--tufte-background);
            stroke-width: 2px;
        }

        .structure-tree .node text {
            font-family: "ET Book", Georgia, serif;
            font-size: 12px;
            fill: var(--tufte-text);
        }

        .structure-tree .link {
            fill: none;
            stroke: var(--tufte-gray);
            stroke-width: 1px;
            stroke-opacity: 0.4;
        }

        .structure-tree .node:hover circle {
            fill: var(--text);
        }

        .structure-tree .node:hover text {
            font-weight: bold;
        }

        .standards-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: var(--spacing);
            margin: var(--spacing) 0;
        }

        .format-section {
            background: var(--tufte-background);
            padding: var(--spacing);
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: var(--spacing);
        }

        .format-title {
            color: var(--highlight);
            font-size: 1.2em;
            margin-bottom: 1rem;
            font-style: italic;
        }

        .format-description {
            color: var(--tufte-text);
            font-size: 0.9em;
            line-height: 1.6;
        }

        .code-sample {
            background: var(--background);
            padding: 1rem;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            color: var(--tufte-text);
            white-space: pre;
            overflow-x: auto;
            margin-top: 1rem;
        }
    </style>
    {{TUFTE_STYLES}}
</head>
<body>
    <div class="data-path"></div>
    <div class="progress-label">Overview</div>

    {{SECTIONS}}

    <div class="scroll-prompt">
        Scroll to explore <span class="scroll-arrow">↓</span>
    </div>

    {{TUFTE_SCRIPTS}}
    
    <script>
        // Initialize scrollama
        const scroller = scrollama();
        
        // Setup scroll interactions
        scroller
            .setup({
                step: '.section',
                offset: 0.5,
                debug: false
            })
            .onStepEnter(response => {
                // Update active section
                document.querySelectorAll('.section').forEach(section => {
                    section.classList.remove('active');
                });
                response.element.classList.add('active');

                // Update nodes
                const nodes = document.querySelectorAll('.node');
                nodes.forEach((node, index) => {
                    if (index <= response.index) {
                        node.classList.add('active');
                    } else {
                        node.classList.remove('active');
                    }
                });

                // Update progress path
                const progress = ((response.index + 1) / document.querySelectorAll('.section').length) * 100;
                document.querySelector('.data-path::after').style.height = `${progress}%`;

                // Update label
                const label = document.querySelector('.progress-label');
                label.textContent = response.element.dataset.title;
                label.classList.add('active');
            })
            .onStepExit(response => {
                if (response.direction === 'up') {
                    response.element.classList.remove('active');
                    document.querySelector('.progress-label').classList.remove('active');
                }
            });

        // Handle resize
        window.addEventListener('resize', scroller.resize);

        // Hide scroll prompt when scrolling starts
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            const prompt = document.querySelector('.scroll-prompt');
            prompt.style.opacity = '0';
            
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                prompt.style.opacity = '0.7';
            }, 1000);
        });

        // Remove any navigation buttons that might have been missed by CSS
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('[class*="nav-"], [class*="control-"]').forEach(el => el.remove());
        });
    </script>
</body>
</html>
"""
        
        # Collect all Tufte content
        all_styles = set()
        all_scripts = []
        sections_html = []
        
        for section, files in self.structure.items():
            section_content = []
            for file in files:
                # Find the file in the section subdirectory
                file_path = None
                for subdir in self.tufte_dir.glob('*'):
                    if subdir.is_dir():
                        potential_path = subdir / file
                        if potential_path.exists():
                            file_path = potential_path
                            break
                
                if file_path:
                    content = self.extract_content(file_path)
                    all_styles.update(content['styles'])
                    all_scripts.extend(content['scripts'])
                    section_content.append(content['content'])
            
            # Create section HTML
            section_html = f"""
            <section class="section" data-step="{section}" data-title="{section.title()}">
                <div class="node"></div>
                <div class="content">
                    <div class="tufte-container">
                        {''.join(section_content)}
                    </div>
                </div>
            </section>
            """
            sections_html.append(section_html)
        
        # Generate scripts HTML
        scripts_html = []
        for script in all_scripts:
            if 'src' in script:
                scripts_html.append(f'<script src="{script["src"]}"></script>')
            elif 'content' in script:
                scripts_html.append(f'<script>{script["content"]}</script>')
        
        # Replace placeholders in template
        html = template.replace('{{TUFTE_STYLES}}', 
                              f'<style>{"".join(all_styles)}</style>')
        html = html.replace('{{TUFTE_SCRIPTS}}', '\n'.join(scripts_html))
        html = html.replace('{{SECTIONS}}', '\n'.join(sections_html))
        
        return html
    
    def save_integrated_html(self, output_file='datawalker-w.html'):
        """Save the integrated HTML to a file."""
        html = self.generate_integrated_html()
        with open(self.base_dir / output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Created integrated file: {output_file}")

def main():
    base_dir = "/Users/gaia/Downloads/WalkabilityIndex"
    integrator = WhiteThemeIntegrator(base_dir)
    integrator.save_integrated_html()

if __name__ == "__main__":
    main()
