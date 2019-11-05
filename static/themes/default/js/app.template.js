const appToggleForm = document.querySelector('#app-toggle')
const appToggleContainer = appToggleForm.parentElement
const appToggleInput = document.querySelector('#app-toggle-input')

const onSubmit = (e) => {
  e.preventDefault
  appToggleInput.checked = !appToggleInput.checked
  appToggleForm.submit()
}

appToggleForm.addEventListener('submit', onSubmit)


/**
 * if javascript is enabled, this script will run and show the toggle button
 */

appToggleContainer.style.display = 'flex';