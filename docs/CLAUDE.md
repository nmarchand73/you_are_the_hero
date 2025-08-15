# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains the development of an interactive fiction game that reads "Choose Your Own Adventure" style books directly from EPUB files. The project uses inkjs (JavaScript port of the ink narrative scripting language) to handle game mechanics and story flow.

## Key Architecture Components

### Core Technical Stack
- **Frontend**: HTML5/CSS3/JavaScript (ES6+) - Static web application
- **Narrative Engine**: inkjs library for interactive storytelling
- **EPUB Processing**: epub.js or JSZip for parsing EPUB files
- **Storage**: localStorage for game saves, IndexedDB for cached converted books

### Data Flow Architecture
1. **EPUB Import**: User uploads .epub → Parser extracts content
2. **Conversion**: EPUB paragraphs → ink script format → inkjs engine
3. **Game Loop**: inkjs state → UI display → user choices → inkjs state update
4. **Persistence**: Game state serialized to localStorage

### EPUB to Ink Conversion
The system converts traditional gamebook paragraph numbers to ink sections:
- EPUB paragraph numbers become ink knots (=== section_X ===)
- "Turn to paragraph Y" becomes ink diverts (-> section_Y)
- Multiple choice options become ink choices (+ [text] -> destination)

## Important Files

### PRD_Interactive_Story_Game.md
Complete Product Requirements Document containing:
- MVP specifications and acceptance criteria
- Technical architecture details
- Development roadmap and success metrics
- UI/UX specifications and responsive design requirements

### doc/WritingWithInk.md
Comprehensive documentation of the ink scripting language including:
- Basic syntax for content, choices, and flow control
- Advanced features like variables, logic, and state tracking
- Examples and best practices for interactive narrative development

### book/ directory
Contains sample EPUB files for testing:
- La-nuit-du-loup-garou.epub - Test gamebook content

## Development Workflow

Since this is an early-stage project with no package.json yet, initial development should focus on:

1. **Environment Setup**: Create package.json with inkjs dependency
2. **Proof of Concept**: Build basic EPUB parser and ink converter
3. **MVP Implementation**: Following the PRD specifications for core features

## Key Technical Considerations

### EPUB Parsing Strategy
- Extract text content from EPUB HTML/XHTML files
- Identify paragraph numbers and cross-references
- Handle various EPUB formatting conventions
- Validate converted ink script syntax

### inkjs Integration
- Initialize Story objects with converted content
- Manage story state persistence and restoration
- Handle choice selection and story continuation
- Implement save/load functionality

### Performance Constraints
- EPUB files limited to 50MB
- Conversion should complete in < 10 seconds
- Mobile-first responsive design
- Browser compatibility: Chrome, Firefox, Safari, Edge

## Game Design Philosophy

This project prioritizes simplicity and accessibility:
- No server backend required (static web app)
- Import existing EPUB gamebooks rather than creating new content
- Minimal UI focusing on reading experience
- Progressive enhancement from basic text to rich interactive features
- memorize this plan