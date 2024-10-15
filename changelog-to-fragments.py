"""
Caveats right now (2024-10-16):
- custom sections like "dropping setuptools support" are not seen (because there
  is no bullet points inside these section, easy to do by hand, there are 2 of them)
- Array API had custom grouping (by class, function, other), so needs to be
  looked at closer. Needs content edition. Also everything is categorized
  other, do we want different tags (maybe feature)?
- 2 entries have two PRs listed 29677 (other PR is 22606) 29143 (other PR is
  27736), probably the content needs to be tweaked there is "By" or/and "and" too many

"""

import re
import textwrap
import warnings
from pathlib import Path

from docutils import nodes
from docutils.core import publish_doctree
from docutils.utils import Reporter


def parse_rst(rst_content):
    doctree = publish_doctree(
        # settings_override is used to avoid showing parsing issues we don't
        # care about, for example for sphinx constructs
        rst_content,
        settings_overrides={"report_level": Reporter.SEVERE_LEVEL + 10},
    )
    return extract_sections_and_bullets(doctree)


def extract_sections_and_bullets(node, level=1):
    result = []

    if isinstance(node, nodes.section):
        title = node.children[0].astext()
        result.append({"type": "section", "level": level, "title": title})
        for child in node.children[1:]:
            result.extend(extract_sections_and_bullets(child, level + 1))

    elif isinstance(node, nodes.bullet_list):
        for item in node.children:
            bullet_text = item.children[0].astext()
            result.append({"type": "bullet", "text": bullet_text})

    elif isinstance(node, nodes.Element):
        for child in node.children:
            result.extend(extract_sections_and_bullets(child, level))

    return result


def section_to_folder(section):
    if section.startswith(":mod:"):
        return re.sub(r":mod:`(.+)`", r"\1", section)

    section_mapping = {
        "Changes impacting many modules": "many-modules",
        "Support for Array API": "array-api",
        "Metadata Routing": "metadata-routing",
    }
    return section_mapping[section]


def get_pr_number(content):
    matches = re.findall(pr_pattern, content)
    if len(matches) > 1:
        warnings.warn(f"More than one PR {matches} in content {content}")

    return matches[-1]


def get_fragment_type(content):
    m = re.match(tag_pattern, content)

    if m is None:
        return "other"

    return tag_to_type[m.group(1)]


def get_fragment_path(section, content):
    pr_number = get_pr_number(content)
    fragment_type = get_fragment_type(content)
    subfolder = section_to_folder(section)
    root_folder = Path("doc/whats_new/upcoming_changes")
    return root_folder / subfolder / f"{pr_number}.{fragment_type}.rst"


def get_fragment_content(content):
    # need to strip spaces hence + r"\s*" in two lines below
    content = re.sub(tag_pattern + r"\s*", "", content)
    content = re.sub(pr_pattern + r"\s*", "", content)
    # Some people use shorthands rather than :user: ...
    user_pattern = r"by(\s+)(:user:`[^`]+`|`[\w ]+`_)"
    content = re.sub(user_pattern, r"By\1\2", content)

    # Need to indent and add the bullet point
    content = textwrap.indent(content, " " * 2)
    return f"-{content[1:]}"


changelog = Path("~/dev/scikit-learn/doc/whats_new/v1.6.rst").expanduser()
# Remove includes which can cause errors and are not necessary for our purposes
content = re.sub(r"\.\. include.+", "", changelog.read_text())
parsed_content = parse_rst(content)

current_section = None
content_by_section = {}
for item in parsed_content:
    if item["type"] == "section":
        current_section = item["title"]
    elif item["type"] == "bullet":
        content_by_section.setdefault(current_section, []).append(item["text"])

pr_pattern = r":pr:`(\d+)`"

tag_to_type = {
    "MajorFeature": "major-feature",
    "Feature": "feature",
    "Efficiency": "efficiency",
    "Enhancement": "enhancement",
    "Fix": "fix",
    "API": "api",
}

joined_tags = "|".join(tag_to_type)
tag_pattern = rf"\|({joined_tags})\|"


for section, content_list in content_by_section.items():
    for content in content_list:
        path = get_fragment_path(section, content)
        path.parent.mkdir(exist_ok=True)
        path.write_text(get_fragment_content(content))
