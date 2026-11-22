// AI disclosure: written with help from Claude (Anthropic), reviewed by the student.
// A stopwatch for the "Log a session" page. Stopping it fills in the minutes field.
(function () {
  const display = document.getElementById("timer-display");
  const toggle = document.getElementById("timer-toggle");
  const finish = document.getElementById("timer-finish");
  const minutes = document.getElementById("minutes");
  if (!display || !toggle || !finish || !minutes) return;

  let elapsed = 0;       // milliseconds accumulated before the current run
  let startedAt = null;  // timestamp of the current run, or null when paused
  let tick = null;

  function total() {
    return elapsed + (startedAt ? Date.now() - startedAt : 0);
  }

  function render() {
    const secs = Math.floor(total() / 1000);
    const h = String(Math.floor(secs / 3600)).padStart(2, "0");
    const m = String(Math.floor((secs % 3600) / 60)).padStart(2, "0");
    const s = String(secs % 60).padStart(2, "0");
    display.textContent = `${h}:${m}:${s}`;
  }

  toggle.addEventListener("click", function () {
    if (startedAt) {                       // pause
      elapsed += Date.now() - startedAt;
      startedAt = null;
      clearInterval(tick);
      toggle.textContent = "Resume timer";
    } else {                               // start or resume
      startedAt = Date.now();
      tick = setInterval(render, 250);
      toggle.textContent = "Pause timer";
    }
    finish.disabled = false;
    render();
  });

  finish.addEventListener("click", function () {
    const ms = total();
    clearInterval(tick);
    startedAt = null;
    elapsed = 0;
    minutes.value = Math.min(1440, Math.max(1, Math.ceil(ms / 60000)));
    toggle.textContent = "Start timer";
    finish.disabled = true;
    render();
    minutes.focus();
  });

  render();
})();
