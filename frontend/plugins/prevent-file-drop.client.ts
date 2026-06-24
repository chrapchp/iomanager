/***************************************************
 * Project:     IOManager
 * Author:      Peter Chrapchynski
 * Date:        2026Jun24
 * History:     2026Jun24 - Initial creation
 ***************************************************/

export default defineNuxtPlugin(() => {
  document.addEventListener('dragover', (e) => e.preventDefault())
  document.addEventListener('drop', (e) => e.preventDefault())
})
