# Managing Workflow Projects

**Source:** https://www.ibm.com/docs/en/dbaoc?topic=automation-managing-projects

## Overview

A project is a set of artifacts that share the same lifecycle and are grouped to solve a particular business problem. You use projects to build, manage, share, and organize these assets. For example, you create, develop, and test your workflow automation and then install it on the server so that people can use it to do their work.

Some actions apply at the project level, the version level, or both.

## Workflow Project Types

### Workflow Automation (automation)
A business automation that contains process and case definitions, artifacts, and asset types that make up processes and service flows.

You can publish some automation artifacts as automation services that you can call and reuse in a consistent way. When published to the catalog, the automation service becomes discoverable across Business Automation Studio to help you drive productivity and customer experiences.

### Template
A predefined starting point that can be used to quickly create a case solution. A template can represent a common-use case pattern, such as a document renewal template, workflow dashboard template, and so on. You can create a template only for a workflow that includes case features.

### Toolkit
A project that contains shared artifacts, which are used at authoring time to create workflow automations. To ensure consistency across applications that are used for the same reason, make artifacts available across automations by putting them in a toolkit. Then, you make those automations depend on that toolkit so they can use those shared artifacts.

Workflow automations can share artifacts from one or more toolkits, and toolkits can share artifacts from other toolkits. Unlike a workflow automation, though, you don't deploy a toolkit; the contents of toolkits that automations depend on are included in the automation when you deploy it.

## Key Topics

- **Converting project artifacts** - Convert project artifacts so they run in container environments
- **Working with projects** - Import and export projects, manage versions and branches
- **Managing servers** - Manage connections to servers for services and documents
- **Managing access** - Control access to repository and projects
- **Installing snapshots** - Install or update process applications or case solutions
- **Administering the Workflow Center index** - Conduct searches on the Workflow Center repository
- **Setting environment variables** - Ensure correct values in each deployment environment
- **Adding support for non-English locales** - Customize case package for PDF generation
- **Modifying toolkit dependencies** - Create, change, or delete toolkit dependencies

---
*Section: Workflow Automation*