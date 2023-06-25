const led = 16;
pinMode(led, OUTPUT);
setInterval(() => {
  digitalToggle(led);
}, 1000);