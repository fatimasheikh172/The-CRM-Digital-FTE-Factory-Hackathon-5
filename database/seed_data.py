"""
Seed Knowledge Base Script

Reads product documentation from context/product-docs.md and seeds
the knowledge_base table with structured entries.
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import List, Dict

import asyncpg
from dotenv import load_dotenv

load_dotenv()

import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_product_docs(docs_path: str) -> List[Dict]:
    """
    Parse product documentation into sections.
    
    Args:
        docs_path: Path to product-docs.md file.
        
    Returns:
        List of dictionaries with title, content, category, tags.
    """
    docs_file = Path(docs_path)
    if not docs_file.exists():
        logger.error(f"Docs file not found: {docs_path}")
        return []
    
    content = docs_file.read_text(encoding='utf-8')
    
    # Split by major sections (## headers)
    sections = re.split(r'\n## ', content)
    
    entries = []
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        lines = section.split('\n')
        
        # First line is the title (may have ### for subsections)
        title_line = lines[0].strip()
        
        # Remove leading ### if present (subsection)
        if title_line.startswith('###'):
            title_line = title_line.lstrip('#').strip()
        
        # Get content (rest of the section)
        section_content = '\n'.join(lines[1:]).strip()
        
        if not title_line or not section_content:
            continue
        
        # Determine category from title
        if ':' in title_line:
            category = title_line.split(':')[0].strip()
        elif i == 0:
            category = 'Introduction'
        else:
            category = 'General'
        
        # Extract tags from title and content
        tags = [
            category.lower().replace(' ', '-'),
            'techcorp',
            'product-docs'
        ]
        
        # Add keywords as tags
        keywords = re.findall(r'\b[A-Z][a-z]+\b', title_line)
        tags.extend([kw.lower() for kw in keywords[:3]])
        
        entries.append({
            'title': title_line,
            'content': section_content,
            'category': category,
            'tags': list(set(tags))  # Remove duplicates
        })
    
    logger.info(f"Parsed {len(entries)} sections from product docs")
    return entries


async def seed_knowledge_base(docs_path: str = 'context/product-docs.md') -> int:
    """
    Seed the knowledge base from product documentation.
    
    Args:
        docs_path: Path to product-docs.md file.
        
    Returns:
        Number of entries inserted.
    """
    logger.info("=" * 60)
    logger.info("TechCorp Customer Success Agent - Knowledge Base Seeding")
    logger.info("=" * 60)
    
    # Parse documentation
    entries = parse_product_docs(docs_path)
    
    if not entries:
        logger.warning("No entries to insert")
        return 0
    
    # Database configuration
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    database = os.getenv('DB_NAME', 'fte_db')
    user = os.getenv('DB_USER', 'fte_user')
    password = os.getenv('DB_PASSWORD', 'fte_password123')
    
    logger.info(f"\nConnecting to PostgreSQL at {host}:{port}/{database}...")
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        logger.info("Connected successfully!")
        
        inserted = 0
        updated = 0
        skipped = 0
        
        for entry in entries:
            try:
                # Check if entry already exists
                existing = await conn.fetchval(
                    "SELECT id FROM knowledge_base WHERE title = $1",
                    entry['title']
                )
                
                if existing:
                    # Update existing entry
                    await conn.execute(
                        """
                        UPDATE knowledge_base
                        SET content = $1, category = $2, tags = $3,
                            updated_at = NOW()
                        WHERE id = $4
                        """,
                        entry['content'],
                        entry['category'],
                        entry['tags'],
                        existing
                    )
                    updated += 1
                    logger.info(f"  ~ Updated: {entry['title'][:50]}...")
                else:
                    # Insert new entry
                    await conn.execute(
                        """
                        INSERT INTO knowledge_base (title, content, category, tags)
                        VALUES ($1, $2, $3, $4)
                        """,
                        entry['title'],
                        entry['content'],
                        entry['category'],
                        entry['tags']
                    )
                    inserted += 1
                    logger.info(f"  + Inserted: {entry['title'][:50]}...")
                    
            except Exception as e:
                skipped += 1
                logger.warning(f"  ! Skipped '{entry['title'][:30]}...': {e}")
        
        await conn.close()
        
        logger.info("\n" + "=" * 60)
        logger.info("Knowledge Base Seeding Complete!")
        logger.info(f"  Inserted: {inserted}")
        logger.info(f"  Updated:  {updated}")
        logger.info(f"  Skipped:  {skipped}")
        logger.info(f"  Total:    {len(entries)}")
        logger.info("=" * 60)
        
        return inserted + updated
        
    except asyncpg.PostgresError as e:
        logger.error(f"PostgreSQL error: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 0


async def verify_seed() -> bool:
    """
    Verify that knowledge base entries were seeded correctly.
    
    Returns:
        True if verification passes.
    """
    logger.info("\nVerifying seeded data...")
    
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', 5432))
    database = os.getenv('DB_NAME', 'fte_db')
    user = os.getenv('DB_USER', 'fte_user')
    password = os.getenv('DB_PASSWORD', 'fte_password123')
    
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        # Count entries
        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
        logger.info(f"  Total entries in knowledge_base: {count}")
        
        # List categories
        categories = await conn.fetch(
            "SELECT category, COUNT(*) as count FROM knowledge_base GROUP BY category ORDER BY count DESC"
        )
        logger.info("  Categories:")
        for cat in categories:
            logger.info(f"    - {cat['category']}: {cat['count']} entries")
        
        # Sample entries
        samples = await conn.fetch(
            "SELECT title, category FROM knowledge_base ORDER BY created_at DESC LIMIT 5"
        )
        logger.info("  Recent entries:")
        for sample in samples:
            logger.info(f"    - [{sample['category']}] {sample['title'][:40]}...")
        
        await conn.close()
        
        return count > 0
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


async def main():
    """Main function to seed and verify knowledge base."""
    count = await seed_knowledge_base()
    if count > 0:
        await verify_seed()
    return count > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
