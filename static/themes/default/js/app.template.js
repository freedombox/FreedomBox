const appForm = document.querySelector('#app-form')
const appToggleContainer = document.querySelector('#app-toggle-container')
const appToggleButton = document.querySelector('#app-toggle-button')
const appToggleInput = document.querySelector('#app-toggle-input')

const onSubmit = (e) => {
  e.preventDefault
  appToggleInput.checked = !appToggleInput.checked
  appForm.submit()
}
appToggleButton.addEventListener('click', onSubmit)

/**
 * if javascript is enabled, this script will run and show the toggle button
 */

appToggleInput.parentElement.style.display = 'none'
appToggleContainer.style.display = 'flex';