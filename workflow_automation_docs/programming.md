# Programming

**Source:** https://www.ibm.com/docs/en/dbaoc?topic=automation-programming

## Overview

Learn about the available APIs, script limitations, and runtime environments.

## Script Limitations

The following table shows the ECMAScript standard, syntax restrictions, and runtime environment that each type of script must follow:

| Script Type | Runtime Environment | ECMAScript Standard | Additional Restrictions |
|-------------|-------------------|-------------------|------------------------|
| Process script | Workflow server | ES5 | None |
| Service script | Workflow server | ES5 | None |
| Client-side human service script | Client browser | ES6 | - Formula/expression only for specific events<br>- JavaScript template literals cannot be used (UI toolkit interprets `$` sign)<br>- No arrow functions in certain contexts |
| Action script | Node.js | ES6 | None |
| View script | Node.js | ES6 | None |

## Key Topics

### REST APIs Programming
Several sets of REST APIs are provided for programming artifacts and services.

### Syntax for Text with Embedded JavaScript
In certain situations, you can combine literal text with parts that are computed dynamically.

### JavaScript API Programming Guide
In the designer, all variables are JavaScript variables so you can use JavaScript code snippets inside your components to improve the behavior of your model. A number of JavaScript libraries are provided. You can also import or create your own libraries.

---
*Section: Workflow Automation*