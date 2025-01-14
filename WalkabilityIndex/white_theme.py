import os
from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

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
        
    def extract_content(self, file_path):
        """Extract content from a Tufte page, preserving original styles."""
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove navigation elements
            for nav in soup.find_all(class_=['nav-buttons', 'control-button', 'controls']):
                nav.decompose()
            
            # Extract styles (keeping original Tufte styling)
            styles = []
            for style in soup.find_all('style'):
                if style.string:
                    styles.append(style.string)
            
            # Extract scripts
            scripts = []
            for script in soup.find_all('script'):
                if script.get('src'):
                    scripts.append({'src': script['src']})
                elif script.string:
                    scripts.append({'content': script.string})
            
            # Extract main content
            main_content = soup.find('body')
            if main_content:
                for script in main_content.find_all('script'):
                    script.decompose()
                content = str(main_content).replace('<body>', '').replace('</body>', '').strip()
                content = f'<div class="tufte-content">{content}</div>'
            
            return {
                'styles': styles,
                'scripts': scripts,
                'content': content
            }
    
    def generate_integrated_html(self):
        """Generate the integrated datawalker HTML with light theme."""
        template = """
<!DOCTYPE html>
<html>
<head>
    <title>Walking Through Data | Atlanta Walkability</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <script src="https://unpkg.com/intersection-observer"></script>
    <script src="https://unpkg.com/scrollama"></script>
    <style>
        :root {
            /* Light theme colors */
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

        /* Tufte-style containers */
        .tufte-container {
            background: var(--tufte-background);
            border-radius: 4px;
            margin: var(--spacing) 0;
            padding: var(--spacing);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            transition: var(--transition);
        }

        .tufte-content {
            color: var(--tufte-text);
        }

        /* Chart styles */
        .chart text {
            fill: var(--tufte-text);
            font-size: 12px;
        }

        .chart .axis line,
        .chart .axis path {
            stroke: var(--tufte-gray);
            stroke-opacity: 0.2;
        }

        .chart .grid line {
            stroke: var(--tufte-gray);
            stroke-opacity: 0.1;
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

        /* Links */
        a {
            color: var(--highlight);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: var(--transition);
        }

        a:hover {
            border-bottom-color: var(--highlight);
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: var(--spacing) 0;
        }

        th, td {
            padding: 0.5rem;
            text-align: left;
            border-bottom: 1px solid #eee;
        }

        th {
            font-weight: 600;
            color: var(--highlight);
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
