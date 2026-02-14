#!/usr/bin/env python3
"""
EPUB to Markdown Post Converter
Converts EPUB files to clean Markdown posts for the Zaya web platform
"""

import os
import random
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


class EpubToPostConverter:
    def __init__(self, posts_dir=None, images_base_dir=None, scripts_dir=None):
        # Set up directories with defaults
        home_dir = Path.home()
        self.posts_dir = posts_dir or home_dir / "Downloads/Zayas/zayaweb/apps/web/src/posts"
        self.images_base_dir = images_base_dir or home_dir / "Downloads/Zayas/zayaweb/apps/web/static/css/img"
        self.scripts_dir = scripts_dir or home_dir / "Downloads/Zayas/zayaweb/apps/web/scripts"
        
        # Ensure directories exist
        os.makedirs(self.posts_dir, exist_ok=True)
        
        # Language mappings for smart image selection
        self.keyword_mappings = {
            "bing": "Bing",
            "cinema": "Cinema",
            "film": "Cinema",
            "movie": "Cinema",
            "psychoanalysis": "Psychoanalysis",
            "psychology": "Psychoanalysis",
            "lacan": "Psychoanalysis",
            "freud": "Psychoanalysis",
            "kb": "KB",
            "ndp": "NdP",
            "anguish": "NdP/Anguish",
            "anime": "NdP/Anime",
            "arthistory": "NdP/ArtHistory",
            "creatures": "NdP/Creatures",
            "mobius": "NdP/Mobius",
            "algorithm": "Bing",
            "digital": "Bing",
            "machine": "Bing",
            "math": "Bing",
            "physics": "Bing",
            "business": "KB",
            "economy": "KB",
            "cv": "KB",
            "career": "KB",
            "language": "NdP",
            "linguistics": "NdP",
            "phonetics": "NdP",
            "quotes": "Psychoanalysis",
            "literature": "Psychoanalysis",
            "book": "Psychoanalysis",
            "theater": "Cinema",
            "volleyball": "KB",
            "dev": "Bing",
            "coding": "Bing",
            "terminal": "Bing",
            "linktree": "KB"
        }

    def slugify(self, text):
        """Convert text to URL-friendly slug"""
        # Convert to ASCII
        text = text.lower()
        # Replace non-alphanumeric with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        # Remove leading/trailing hyphens
        text = text.strip('-')
        # Return slug (keep lowercase for URLs, don't capitalize)
        return text

    def get_random_image(self, directory, pattern="*.png"):
        """Get random image from directory"""
        if os.path.exists(directory):
            import glob
            images = glob.glob(os.path.join(directory, pattern))
            images.extend(glob.glob(os.path.join(directory, "*.jpg")))
            images.extend(glob.glob(os.path.join(directory, "*.jpeg")))
            
            if images:
                random_image = random.choice(images)
                # Convert to web path
                return str(Path(random_image).relative_to(Path(self.images_base_dir).parent.parent))
        return None

    def select_smart_image(self, title, slug=""):
        """Smartly select image based on title content"""
        lowercase_title = title.lower()
        combined_text = f"{lowercase_title} {slug.lower()}"
        
        # Check for keyword matches
        for keyword, folder in self.keyword_mappings.items():
            if keyword in combined_text:
                full_path = os.path.join(self.images_base_dir, folder)
                if os.path.exists(full_path):
                    # Determine pattern based on folder
                    if folder == "Bing":
                        image = self.get_random_image(full_path, "bing*.png")
                    else:
                        image = self.get_random_image(full_path)
                    
                    if image:
                        return f"/{image}"
        
        # Default fallback
        default_image = self.get_random_image(os.path.join(self.images_base_dir, "Bing"), "bing*.png")
        if default_image:
            return f"/{default_image}"
        
        # Ultimate fallback
        return "/css/img/default.png"

    def extract_title_from_epub(self, epub_path):
        """Extract title from EPUB file"""
        try:
            # Try using pandoc to get metadata
            result = subprocess.run(
                ['pandoc', str(epub_path), '--to', 'plain', '--quiet'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Look for title in metadata or first heading
            # lines = result.stdout.split('\n')
            
            # # Check for markdown headings first
            # for line in lines[:20]:
            #     if line.startswith('# '):
            #         return line[2:].strip()
            
            # # Then check for any non-empty line that's not too long
            # for line in lines[:10]:
            #     line = line.strip()
            #     if line and len(line) < 100 and not line.startswith('['):
            #         return line
            
        except Exception as e:
            print(f"Warning: Could not extract title from {epub_path}: {e}")
        
        # Fallback to filename
        filename = Path(epub_path).stem
        # Clean up filename: replace hyphens and underscores with spaces
        title = filename.replace('-', ' ').replace('_', ' ').title()
        title = ' '.join(word.capitalize() for word in title.split())
        return title

    def clean_markdown(self, content):
        """
        Clean up markdown content after pandoc conversion
        Removes HTML tags, special patterns, and formats properly
        """
        original_lines = content.split('\n')
        total_lines = len(original_lines)
        
        # 1. Remove content between ``` markers (code blocks)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        
        # 2. Remove patterns starting with {#c
        content = re.sub(r'\{#c[^}]+\}', '', content)
        
        # 3. Add slash next to single quotes: replace backslash followed by single quote with just single quote
        content = re.sub(r"\\'", "'", content)
        
        # 4. Remove specific patterns from the example
        patterns_to_remove = [
            r'! ?\[.*?\]\(.*?\)',  # ! [](filename) patterns
            r'\[\]{#[^}]+}',  # []{#id.xhtml} patterns
            r'```\{=html\}.*?```',  # ```{=html} blocks
            r'``\{=html\}',  # Remove ``{=html} (opening part)
            r'\{=html\}',  # Remove standalone {=html}
            r'<[^>]+>',  # HTML tags
            r'::: \{#[^}]+\}.*?(?=:::|$)',  # ::: {#id} blocks
            r':::',  # Remaining ::: markers
            r'#  +\{#[^}]+\}',  # #  {#id} patterns
            r'\{#[^}]+\}',  # Any remaining {#id} patterns
            r'style="[^"]*"',  # style attributes
            r'dir="[^"]*"',  # dir attributes
            r'lang="[^"]*"',  # lang attributes
            r'\.unnumbered',  # .unnumbered class
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.DOTALL)
    
        
        # 4. Split into lines for further processing
        lines = content.split('\n')
        cleaned_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines or lines that are just whitespace
            if not line:
                i += 1
                continue
            
            # Check if line is a header (starts with #)
            if line.startswith('#'):
                # Ensure header has space after #
                line = re.sub(r'#+', lambda m: m.group() + ' ', line)
                line = line.rstrip()
                cleaned_lines.append(line)
                cleaned_lines.append('')  # Add blank line after header
                i += 1
                continue
            
            # Check if line is a verse marker like [Verse 1] or [Куплет 1]
            if re.match(r'^\[.*\]$', line):
                cleaned_lines.append(line)
                cleaned_lines.append('')  # Add blank line after verse marker
                i += 1
                continue
            
            # Regular text line
            cleaned_lines.append(line)
            
            # Check if we need to add a blank line
            # Add blank line if next line exists and is not empty
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    # Don't add blank line if next line is a header or verse marker
                    if not (next_line.startswith('#') or re.match(r'^\[.*\]$', next_line)):
                        cleaned_lines.append('')  # Add blank line between regular text lines
            
            i += 1
        
        # 5. Join lines and clean up multiple blank lines
        content = '\n'.join(cleaned_lines)
        
        # Replace 3+ blank lines with just 2
        content = re.sub(r'\n{3,}', '\n\n', content)
        content = re.sub(r'\n{1,}', '\n\n', content)

        # Remove blank lines at start and end
        content = content.strip()
        
        # 6. Clean up punctuation spacing
        content = re.sub(r'\s+([,.!?;:])', r'\1', content)  # Remove space before punctuation
        content = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', content)  # Add space after punctuation if missing
        
        return content

    def convert_epub_to_post(self, epub_path, custom_title=None, custom_slug=None):
        """
        Convert EPUB to markdown post and move to posts directory
        Returns: (success, post_path, title, slug)
        """
        try:
            # Get title - if custom title not provided, extract from EPUB
            if custom_title:
                title = custom_title
            else:
                title = self.extract_title_from_epub(epub_path)
                print(f"Auto-detected title: {title}")
            
            # Generate slug
            if custom_slug:
                slug = self.slugify(custom_slug)
            else:
                slug = self.slugify(title)
            
            # Create temporary file for markdown output
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False) as tmp_file:
                temp_md_path = tmp_file.name
            
            # Convert EPUB to markdown using pandoc
            print(f"Converting {epub_path} to markdown...")
            subprocess.run([
                'pandoc',
                str(epub_path),
                '-f', 'epub',
                '-t', 'markdown',
                '--wrap=preserve',
                '--extract-media', str(Path(temp_md_path).parent),
                '-o', temp_md_path
            ], check=True, timeout=60)
            
            # Read the converted markdown
            with open(temp_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up the markdown
            cleaned_content = self.clean_markdown(content)
            
            # Select image
            img_url = self.select_smart_image(title, slug)
            
            # Get current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Create post content with frontmatter
            post_content = f"""---
title: "{title}"
imgUrl: "{img_url}"
youtubeId: ""
publishedAt: "{current_date}"
updatedAt: "{current_date}"
summary: "Converted from EPUB: {Path(epub_path).name}"
---

{cleaned_content}
"""
            
            # Write final post
            post_path = Path(self.posts_dir) / f"{slug}.md"
            
            # Check if post already exists
            if post_path.exists():
                response = input(f"Post {slug}.md already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print("Skipping...")
                    os.unlink(temp_md_path)
                    return False, None, title, slug
            
            with open(post_path, 'w', encoding='utf-8') as f:
                f.write(post_content)
            
            # Clean up temp file
            os.unlink(temp_md_path)
            
            print(f"✅ Successfully created post: {post_path}")
            return True, str(post_path), title, slug
            
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout converting {epub_path}")
            return False, None, None, None
        except subprocess.CalledProcessError as e:
            print(f"❌ Pandoc error for {epub_path}: {e}")
            return False, None, None, None
        except Exception as e:
            print(f"❌ Unexpected error converting {epub_path}: {e}")
            return False, None, None, None

    def convert_folder(self, folder_path, pattern="*.epub"):
        """Convert all EPUBs in a folder to posts"""
        import glob
        
        folder = Path(folder_path)
        epub_files = list(folder.glob(pattern))
        
        if not epub_files:
            print(f"No EPUB files found in {folder_path} matching {pattern}")
            return []
        
        print(f"Found {len(epub_files)} EPUB files to convert")
        results = []
        
        for i, epub_file in enumerate(epub_files, 1):
            print(f"\n[{i}/{len(epub_files)}] Processing: {epub_file.name}")
            
            # Show auto-detected title first
            auto_title = self.extract_title_from_epub(epub_file)
            print(f"Auto-detected title: {auto_title}")
            
            # Ask for custom title/slug for each file (optional)
            use_custom = input("Use custom title/slug? (y/N): ").strip().lower()
            custom_title = None
            custom_slug = None
            
            if use_custom == 'y':
                custom_title = input(f"Enter title (Enter to use '{auto_title}'): ").strip()
                if not custom_title:
                    custom_title = auto_title
                
                custom_slug = input("Enter slug (Enter to generate from title): ").strip() or None
            else:
                custom_title = auto_title
            
            success, post_path, title, slug = self.convert_epub_to_post(
                epub_file, 
                custom_title=custom_title,
                custom_slug=custom_slug
            )
            
            results.append({
                'epub': str(epub_file),
                'success': success,
                'post': post_path,
                'title': title,
                'slug': slug
            })
        
        # Summary
        print("\n" + "="*50)
        print("CONVERSION SUMMARY")
        print("="*50)
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"✅ Successful: {len(successful)}")
        for r in successful:
            print(f"   - {r['title']} -> {Path(r['post']).name}")
        
        if failed:
            print(f"❌ Failed: {len(failed)}")
            for r in failed:
                print(f"   - {Path(r['epub']).name}")
        
        return results


def main():
    """Command-line interface for epub2post.py"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert EPUB files to Markdown posts')
    parser.add_argument('input', help='Input EPUB file or folder')
    parser.add_argument('--title', '-t', help='Custom title for the post')
    parser.add_argument('--slug', '-s', help='Custom slug for the post')
    parser.add_argument('--pattern', '-p', default='*.epub', help='File pattern when input is a folder (default: *.epub)')
    parser.add_argument('--posts-dir', help='Custom posts directory')
    parser.add_argument('--images-dir', help='Custom images base directory')
    
    args = parser.parse_args()
    
    converter = EpubToPostConverter(
        posts_dir=args.posts_dir,
        images_base_dir=args.images_dir
    )
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # Single file
        success, post_path, title, slug = converter.convert_epub_to_post(
            input_path,
            custom_title=args.title,
            custom_slug=args.slug
        )
        if success:
            print(f"\n✅ Post created: {post_path}")
        else:
            print(f"\n❌ Conversion failed for {input_path}")
            sys.exit(1)
    
    elif input_path.is_dir():
        # Folder
        converter.convert_folder(input_path, args.pattern)
    
    else:
        print(f"Error: {input_path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()