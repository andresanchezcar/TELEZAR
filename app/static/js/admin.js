(function () {
  "use strict";

  var sidebar = document.getElementById("sidebar");
  var toggle = document.getElementById("sidebar-toggle");
  var overlay = document.getElementById("sidebar-overlay");

  if (sidebar && toggle) {
    var openSidebar = function () {
      sidebar.classList.add("open");
      document.body.classList.add("sidebar-open");
      if (overlay) overlay.classList.add("show");
    };
    var closeSidebar = function () {
      sidebar.classList.remove("open");
      document.body.classList.remove("sidebar-open");
      if (overlay) overlay.classList.remove("show");
    };

    toggle.addEventListener("click", function () {
      if (sidebar.classList.contains("open")) closeSidebar();
      else openSidebar();
    });

    if (overlay) overlay.addEventListener("click", closeSidebar); 

    sidebar.querySelectorAll(".side-link").forEach(function (link) {
      link.addEventListener("click", function () {
        if (window.innerWidth <= 960) closeSidebar();
      });
    });
  }

  document.querySelectorAll(".flash-close").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var flash = btn.closest(".flash");
      if (flash) flash.remove();
    });
  });

  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) {
        event.preventDefault();
      }
    });
  });

  var conditionalFields = document.querySelectorAll("[data-show-if]");
  if (conditionalFields.length) {
    var form = conditionalFields[0].closest("form") || document;

    var applyConditions = function () {
      conditionalFields.forEach(function (block) {
        var rules;
        try {
          rules = JSON.parse(block.getAttribute("data-show-if"));
        } catch (e) {
          return;
        }
        var visible = Object.keys(rules).every(function (name) {
          var control = form.querySelector('[name="' + name + '"]');
          if (!control) return true;
          var allowed = rules[name];
          if (!Array.isArray(allowed)) allowed = [allowed];
          return allowed.indexOf(control.value) !== -1;
        });
        block.classList.toggle("is-hidden", !visible);
        block.querySelectorAll("[required], [data-required]").forEach(function (el) {
          if (!el.hasAttribute("data-required")) el.setAttribute("data-required", "1");
          if (visible) el.setAttribute("required", "required");
          else el.removeAttribute("required");
        });
      });
    };

    form.addEventListener("change", applyConditions);
    applyConditions();
  }

  var testRows = document.getElementById("test-rows");
  var testTemplate = document.getElementById("test-row-template");
  var addTestBtn = document.querySelector("[data-add-test]");

  if (testRows && testTemplate && addTestBtn) {
    var nextIndex = testRows.querySelectorAll("tr").length;

    var renumber = function () {
      testRows.querySelectorAll("tr").forEach(function (row, i) {
        var no = row.querySelector('input[name$="-no"]');
        if (no) no.value = i + 1;
      });
    };

    var bindRemove = function (row) {
      var removeBtn = row.querySelector("[data-remove-test]");
      if (removeBtn) {
        removeBtn.addEventListener("click", function () {
          row.remove();
          renumber();
        });
      }
    };

    testRows.querySelectorAll("tr").forEach(bindRemove);
    renumber();

    addTestBtn.addEventListener("click", function () {
      var html = testTemplate.innerHTML.replace(/__INDEX__/g, nextIndex);
      nextIndex += 1;
      var wrapper = document.createElement("tbody");
      wrapper.innerHTML = html.trim();
      var row = wrapper.querySelector("tr");
      if (!row) return;
      testRows.appendChild(row);
      bindRemove(row);
      renumber();
      var firstInput = row.querySelector('input[name$="-wavelength"]') || row.querySelector("input");
      if (firstInput) firstInput.focus();
    });
  }

  /* ------------------ Equipos de prueba (patron) ------------------ */
  var repeatList = document.querySelector("[data-repeat-list]");
  if (repeatList) {
    var repeatRows = repeatList.querySelector("[data-repeat-rows]");
    var repeatHidden = repeatList.querySelector("[data-repeat-hidden]");
    var repeatAdd = repeatList.querySelector("[data-repeat-add]");

    var makeRepeatRow = function (value) {
      var row = document.createElement("div");
      row.className = "repeat-row";

      var input = document.createElement("input");
      input.className = "form-control";
      input.type = "text";
      input.setAttribute("data-repeat-item", "");
      input.placeholder = "Ej: Promax OD-405 (serie TZC0738)";
      input.value = value || "";

      var remove = document.createElement("button");
      remove.className = "btn btn-danger btn-xs";
      remove.type = "button";
      remove.setAttribute("data-repeat-remove", "");
      remove.innerHTML = "&times;";
      remove.addEventListener("click", function () {
        row.remove();
      });

      row.appendChild(input);
      row.appendChild(remove);
      return row;
    };

    repeatRows.querySelectorAll(".repeat-row").forEach(function (row) {
      var remove = row.querySelector("[data-repeat-remove]");
      if (remove) {
        remove.addEventListener("click", function () {
          row.remove();
        });
      }
    });

    if (!repeatRows.querySelector(".repeat-row")) {
      repeatRows.appendChild(makeRepeatRow(""));
    }

    if (repeatAdd) {
      repeatAdd.addEventListener("click", function () {
        var row = makeRepeatRow("");
        repeatRows.appendChild(row);
        var input = row.querySelector("[data-repeat-item]");
        if (input) input.focus();
      });
    }

    if (repeatHidden && repeatHidden.form) {
      repeatHidden.form.addEventListener("submit", function () {
        var items = [];
        repeatRows.querySelectorAll("[data-repeat-item]").forEach(function (input) {
          var value = (input.value || "").trim();
          if (value) items.push(value);
        });
        repeatHidden.value = JSON.stringify(items);
      });
    }
  }

  /* ---------------------- Certificado OTDR ---------------------- */
  var otdrRoot = document.querySelector("[data-otdr]");
  var otdrHidden = document.getElementById("otdr_data");

  if (otdrRoot && otdrHidden) {
    var SAMPLES = 5;

    var str = function (v) {
      return v === null || v === undefined ? "" : String(v);
    };
    var esc = function (v) {
      return str(v)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    };
    var num = function (v) {
      if (v === null || v === undefined) return null;
      var s = String(v).trim().replace(",", ".");
      if (!s) return null;
      var n = Number(s);
      return isNaN(n) ? null : n;
    };
    var values = function (samples) {
      return (samples || []).map(num).filter(function (n) {
        return n !== null;
      });
    };
    var meanOf = function (samples) {
      var nums = values(samples);
      if (!nums.length) return null;
      var sum = nums.reduce(function (a, b) {
        return a + b;
      }, 0);
      return sum / nums.length;
    };
    var stdevOf = function (samples) {
      var nums = values(samples);
      if (nums.length < 2) return null;
      var m = nums.reduce(function (a, b) {
        return a + b;
      }, 0) / nums.length;
      var variance = nums.reduce(function (a, b) {
        return a + (b - m) * (b - m);
      }, 0) / (nums.length - 1);
      return Math.sqrt(variance);
    };
    var fmt3 = function (n) {
      return n === null ? "" : n.toFixed(3);
    };

    var normCal = function (type) {
      return function (cal) {
        cal = cal && typeof cal === "object" ? cal : {};
        var rows = Array.isArray(cal.rows)
          ? cal.rows.map(function (r) {
              r = r && typeof r === "object" ? r : {};
              var src = Array.isArray(r.samples) ? r.samples : [];
              var samples = [];
              for (var i = 0; i < SAMPLES; i += 1) samples.push(str(src[i]));
              if (type === "distance") {
                return { pattern: str(r.pattern), initial: str(r.initial), samples: samples };
              }
              return { event: str(r.event), pattern: str(r.pattern), samples: samples };
            })
          : [];
        return { wavelength: str(cal.wavelength), rows: rows };
      };
    };

    var newRow = function (type) {
      var samples = [];
      for (var i = 0; i < SAMPLES; i += 1) samples.push("");
      if (type === "distance") {
        return { pattern: "", initial: "", samples: samples };
      }
      return { event: "", pattern: "", samples: samples };
    };

    var otdr = (function () {
      var data = {};
      try {
        data = otdrHidden.value ? JSON.parse(otdrHidden.value) : {};
      } catch (e) {
        data = {};
      }
      if (!data || typeof data !== "object") data = {};
      var env = data.environment && typeof data.environment === "object" ? data.environment : {};
      return {
        environment: {
          temp: str(env.temp),
          temp_tol: str(env.temp_tol),
          humidity: str(env.humidity),
          humidity_tol: str(env.humidity_tol),
        },
        distance: Array.isArray(data.distance) ? data.distance.map(normCal("distance")) : [],
        attenuation: Array.isArray(data.attenuation) ? data.attenuation.map(normCal("attenuation")) : [],
        patterns: Array.isArray(data.patterns) ? data.patterns.map(str) : [],
        methods: Array.isArray(data.methods) ? data.methods.map(str) : [],
      };
    })();

    var rowHtml = function (type, ri, r) {
      var isDist = type === "distance";
      var cells =
        '<td><input class="form-control otdr-auto" data-field="' + (isDist ? "pattern" : "event") +
        '" value="' + esc(str(ri + 1)) + '" readonly tabindex="-1"></td>' +
        '<td><input class="form-control" data-field="' + (isDist ? "initial" : "pattern") +
        '" value="' + esc(isDist ? r.initial : r.pattern) + '"></td>';
      for (var s = 0; s < SAMPLES; s += 1) {
        cells +=
          '<td><input class="form-control" data-field="sample" data-si="' + s +
          '" value="' + esc(r.samples[s]) + '"></td>';
      }
      cells +=
        '<td class="otdr-calc" data-calc="mean">' + fmt3(meanOf(r.samples)) + "</td>" +
        '<td class="otdr-calc" data-calc="stdev">' + fmt3(stdevOf(r.samples)) + "</td>" +
        '<td class="td-actions"><button class="btn btn-danger btn-xs" type="button" data-row-remove>&times;</button></td>';
      return '<tr data-row data-ri="' + ri + '">' + cells + "</tr>";
    };

    var groupHtml = function (type, gi, g) {
      var isDist = type === "distance";
      var head =
        "<thead><tr><th>" + (isDist ? "Patrón" : "Evento") + "</th><th>" +
        (isDist ? "Valor inicial" : "Valor patrón") + "</th>";
      for (var s = 0; s < SAMPLES; s += 1) head += "<th>Muestra " + (s + 1) + "</th>";
      head += '<th>Promedio</th><th>Desviación ST</th><th class="td-actions"></th></tr></thead>';
      var body =
        "<tbody>" +
        g.rows
          .map(function (r, ri) {
            return rowHtml(type, ri, r);
          })
          .join("") +
        "</tbody>";
      return (
        '<div class="otdr-group" data-group="' + type + '" data-gi="' + gi + '">' +
        '<div class="otdr-group-head">' +
        '<div class="form-group"><label>Longitud de onda (nm)</label>' +
        '<input class="form-control" data-field="wavelength" value="' + esc(g.wavelength) +
        '" placeholder="1310"></div>' +
        '<button class="btn btn-danger btn-sm" type="button" data-group-remove>Eliminar calibración</button>' +
        "</div>" +
        '<div class="table-wrap"><table class="data-table rows-table otdr-table">' +
        head + body + "</table></div>" +
        '<button class="btn btn-outline btn-sm" type="button" data-row-add>+ Agregar fila</button>' +
        "</div>"
      );
    };

    var renderOtdr = function () {
      ["distance", "attenuation"].forEach(function (type) {
        var host = otdrRoot.querySelector('[data-otdr-groups="' + type + '"]');
        if (!host) return;
        host.innerHTML = otdr[type]
          .map(function (g, gi) {
            return groupHtml(type, gi, g);
          })
          .join("");
      });
      ["patterns", "methods"].forEach(function (name) {
        var host = otdrRoot.querySelector('[data-otdr-list="' + name + '"]');
        if (!host) return;
        host.innerHTML = otdr[name]
          .map(function (v, i) {
            return (
              '<div class="otdr-simple-row" data-li="' + i + '">' +
              '<input class="form-control" data-field="value" value="' + esc(v) + '">' +
              '<button class="btn btn-danger btn-xs" type="button" data-list-remove>&times;</button>' +
              "</div>"
            );
          })
          .join("");
      });
    };

    var refreshCalc = function (row, samples) {
      var meanCell = row.querySelector('[data-calc="mean"]');
      var stdCell = row.querySelector('[data-calc="stdev"]');
      if (meanCell) meanCell.textContent = fmt3(meanOf(samples));
      if (stdCell) stdCell.textContent = fmt3(stdevOf(samples));
    };

    otdrRoot.addEventListener("input", function (event) {
      var input = event.target;
      if (input.hasAttribute("data-env")) {
        otdr.environment[input.getAttribute("data-env")] = input.value;
        return;
      }
      if (!input.matches("[data-field]")) return;

      var listHost = input.closest("[data-otdr-list]");
      if (listHost) {
        var item = input.closest("[data-li]");
        otdr[listHost.getAttribute("data-otdr-list")][parseInt(item.getAttribute("data-li"), 10)] =
          input.value;
        return;
      }

      var group = input.closest("[data-group]");
      if (!group) return;
      var type = group.getAttribute("data-group");
      var cal = otdr[type][parseInt(group.getAttribute("data-gi"), 10)];
      var field = input.getAttribute("data-field");
      if (field === "wavelength") {
        cal.wavelength = input.value;
        return;
      }
      var row = input.closest("[data-row]");
      if (!row) return;
      var data = cal.rows[parseInt(row.getAttribute("data-ri"), 10)];
      if (field === "sample") {
        data.samples[parseInt(input.getAttribute("data-si"), 10)] = input.value;
        refreshCalc(row, data.samples);
      } else {
        data[field] = input.value;
      }
    });

    otdrRoot.addEventListener("click", function (event) {
      var btn = event.target.closest(
        "[data-otdr-add],[data-group-remove],[data-row-add],[data-row-remove],[data-list-remove]"
      );
      if (!btn) return;

      if (btn.hasAttribute("data-otdr-add")) {
        var kind = btn.getAttribute("data-otdr-add");
        if (kind === "patterns" || kind === "methods") otdr[kind].push("");
        else otdr[kind].push({ wavelength: "", rows: [newRow(kind)] });
      } else if (btn.hasAttribute("data-group-remove")) {
        var g = btn.closest("[data-group]");
        otdr[g.getAttribute("data-group")].splice(parseInt(g.getAttribute("data-gi"), 10), 1);
      } else if (btn.hasAttribute("data-row-add")) {
        var ag = btn.closest("[data-group]");
        otdr[ag.getAttribute("data-group")][parseInt(ag.getAttribute("data-gi"), 10)].rows.push(
          newRow(ag.getAttribute("data-group"))
        );
      } else if (btn.hasAttribute("data-row-remove")) {
        var rr = btn.closest("[data-row]");
        var rg = btn.closest("[data-group]");
        otdr[rg.getAttribute("data-group")][parseInt(rg.getAttribute("data-gi"), 10)].rows.splice(
          parseInt(rr.getAttribute("data-ri"), 10),
          1
        );
      } else if (btn.hasAttribute("data-list-remove")) {
        var li = btn.closest("[data-li]");
        var lhost = btn.closest("[data-otdr-list]");
        otdr[lhost.getAttribute("data-otdr-list")].splice(parseInt(li.getAttribute("data-li"), 10), 1);
      }
      renderOtdr();
    });

    var pruneOtdr = function () {
      var keepRow = function (type, r) {
        if (type === "distance") {
          return str(r.initial).trim() !== "" || values(r.samples).length > 0;
        }
        return str(r.pattern).trim() !== "" || values(r.samples).length > 0;
      };
      ["distance", "attenuation"].forEach(function (type) {
        var groups = [];
        otdr[type].forEach(function (g) {
          var rows = (g.rows || []).filter(function (r) {
            return keepRow(type, r);
          });
          if (!rows.length) return;
          rows.forEach(function (r, i) {
            if (type === "distance") r.pattern = String(i + 1);
            else r.event = String(i + 1);
          });
          groups.push({ wavelength: str(g.wavelength), rows: rows });
        });
        otdr[type] = groups;
      });
      otdr.patterns = otdr.patterns.filter(function (v) {
        return str(v).trim() !== "";
      });
      otdr.methods = otdr.methods.filter(function (v) {
        return str(v).trim() !== "";
      });
    };

    ["temp", "temp_tol", "humidity", "humidity_tol"].forEach(function (key) {
      var el = otdrRoot.querySelector('[data-env="' + key + '"]');
      if (el) el.value = otdr.environment[key] || "";
    });

    if (otdrHidden.form) {
      otdrHidden.form.addEventListener("submit", function () {
        pruneOtdr();
        otdrHidden.value = JSON.stringify(otdr);
      });
    }

    renderOtdr();
  }

  /* ------------------ Certificado de ajuste mecanico ------------------ */
  var mechRoot = document.querySelector("[data-mech]");
  var mechHidden = document.getElementById("mech_data");

  if (mechRoot && mechHidden) {
    var mechForm = mechHidden.form || mechRoot.closest("form");

    var source = {};
    try {
      source = JSON.parse(mechRoot.getAttribute("data-patrones") || "{}") || {};
    } catch (e) {
      source = {};
    }

    var legalEl = document.getElementById("f-mech_legal");
    var actionRows = document.querySelector("[data-mech-action-rows]");
    var actionAdd = document.querySelector("[data-mech-action-add]");
    var patronRows = document.getElementById("mech-patron-rows");
    var patronAdd = document.querySelector("[data-mech-patron-add]");

    var PATRON_FIELDS = [
      ["descripcion", "Descripción"],
      ["fabricante", "Fabricante"],
      ["modelo", "Modelo"],
      ["serie", "N° de serie"],
      ["certificado", "N° certificado"],
      ["vence", "Vence"],
    ];

    var makeActionRow = function (value) {
      var row = document.createElement("div");
      row.className = "repeat-row";
      var input = document.createElement("input");
      input.className = "form-control";
      input.type = "text";
      input.setAttribute("data-mech-action", "");
      input.value = value || "";
      var remove = document.createElement("button");
      remove.className = "btn btn-danger btn-xs";
      remove.type = "button";
      remove.innerHTML = "&times;";
      remove.addEventListener("click", function () {
        row.remove();
      });
      row.appendChild(input);
      row.appendChild(remove);
      return row;
    };

    var makePatronRow = function (obj) {
      obj = obj || {};
      var tr = document.createElement("tr");
      PATRON_FIELDS.forEach(function (pair) {
        var td = document.createElement("td");
        var input = document.createElement("input");
        input.className = "form-control";
        input.type = "text";
        input.setAttribute("data-mp", pair[0]);
        input.placeholder = pair[1];
        input.value = obj[pair[0]] || "";
        td.appendChild(input);
        tr.appendChild(td);
      });
      var tdActions = document.createElement("td");
      tdActions.className = "td-actions";
      var remove = document.createElement("button");
      remove.className = "btn btn-danger btn-xs";
      remove.type = "button";
      remove.innerHTML = "&times;";
      remove.addEventListener("click", function () {
        tr.remove();
      });
      tdActions.appendChild(remove);
      tr.appendChild(tdActions);
      return tr;
    };

    var bindActionRemove = function (row) {
      var remove = row.querySelector("[data-mech-action-remove]");
      if (remove) {
        remove.addEventListener("click", function () {
          row.remove();
        });
      }
    };

    if (actionRows) {
      actionRows.querySelectorAll(".repeat-row").forEach(bindActionRemove);
      if (actionAdd) {
        actionAdd.addEventListener("click", function () {
          var row = makeActionRow("");
          actionRows.appendChild(row);
          var input = row.querySelector("[data-mech-action]");
          if (input) input.focus();
        });
      }
    }

    if (patronRows) {
      if (!patronRows.querySelector("tr")) patronRows.appendChild(makePatronRow({}));
      if (patronAdd) {
        patronAdd.addEventListener("click", function () {
          var tr = makePatronRow({});
          patronRows.appendChild(tr);
          var input = tr.querySelector("[data-mp='serie']");
          if (input) input.focus();
        });
      }
      patronRows.addEventListener("input", function (event) {
        var input = event.target;
        if (!input.matches || !input.matches('[data-mp="serie"]')) return;
        var key = (input.value || "").trim().toUpperCase();
        var info = source[key];
        if (!info) return;
        var tr = input.closest("tr");
        if (!tr) return;
        PATRON_FIELDS.forEach(function (pair) {
          if (pair[0] === "serie") return;
          var value = info[pair[0]];
          if (!value) return;
          var field = tr.querySelector('[data-mp="' + pair[0] + '"]');
          if (field) field.value = value;
        });
      });
    }

    /* Filtra "Dispositivo a certificar" segun "Tipo de certificado". */
    var certSel = mechForm ? mechForm.querySelector('[name="cert_type"]') : null;
    var devSel = mechForm ? mechForm.querySelector('[name="device_type"]') : null;
    var DEVICE_MAP = {
      calibracion: ["opm", "otdr"],
      mecanica: ["mecanica"],
    };
    var refreshConditions = function () {
      if (mechForm) mechForm.dispatchEvent(new Event("change", { bubbles: true }));
    };
    var deviceOptions = [];
    if (devSel) {
      deviceOptions = Array.prototype.map.call(devSel.options, function (opt) {
        return { value: opt.value, label: opt.text };
      });
    }
    var rebuildDeviceOptions = function (allowed, preferred) {
      if (!devSel) return;
      var current = preferred || devSel.value;
      devSel.innerHTML = "";
      allowed.forEach(function (value) {
        var match = null;
        for (var i = 0; i < deviceOptions.length; i += 1) {
          if (deviceOptions[i].value === value) { match = deviceOptions[i]; break; }
        }
        if (!match) return;
        var option = document.createElement("option");
        option.value = match.value;
        option.textContent = match.label;
        devSel.appendChild(option);
      });
      if (allowed.indexOf(current) !== -1) devSel.value = current;
    };
    var applyDeviceFilter = function () {
      if (!certSel || !devSel) return;
      var allowed = DEVICE_MAP[certSel.value];
      if (allowed) rebuildDeviceOptions(allowed, devSel.value);
    };
    if (certSel && devSel) {
      certSel.addEventListener("change", function () {
        applyDeviceFilter();
        if (certSel.value === "mecanica") devSel.value = "mecanica";
        refreshConditions();
      });
      devSel.addEventListener("change", function () {
        if (devSel.value === "mecanica") {
          certSel.value = "mecanica";
          rebuildDeviceOptions(DEVICE_MAP.mecanica, "mecanica");
        } else if (certSel.value === "mecanica") {
          certSel.value = "calibracion";
          rebuildDeviceOptions(DEVICE_MAP.calibracion, devSel.value);
        }
        refreshConditions();
      });
      applyDeviceFilter();
    }

    var readMech = function () {
      var data = {
        legal: "",
        actions: [],
        patrones: [],
        environment: { temp: "", temp_tol: "", humidity: "", humidity_tol: "" },
      };
      if (legalEl) data.legal = (legalEl.value || "").trim();

      if (actionRows) {
        actionRows.querySelectorAll("[data-mech-action]").forEach(function (input) {
          var value = (input.value || "").trim();
          if (value) data.actions.push(value);
        });
      }

      if (patronRows) {
        patronRows.querySelectorAll("tr").forEach(function (tr) {
          var row = {};
          var has = false;
          PATRON_FIELDS.forEach(function (pair) {
            var field = tr.querySelector('[data-mp="' + pair[0] + '"]');
            var value = field ? (field.value || "").trim() : "";
            row[pair[0]] = value;
            if (value) has = true;
          });
          if (has) data.patrones.push(row);
        });
      }

      mechForm.querySelectorAll("[data-mc-env]").forEach(function (input) {
        var key = input.getAttribute("data-mc-env");
        if (key in data.environment) data.environment[key] = (input.value || "").trim();
      });

      return data;
    };

    if (mechForm) {
      mechForm.addEventListener("submit", function () {
        if (!devSel || devSel.value !== "mecanica") {
          mechHidden.value = "";
          return;
        }
        var data = readMech();
        var hasEnv =
          data.environment.temp ||
          data.environment.temp_tol ||
          data.environment.humidity ||
          data.environment.humidity_tol;
        var empty =
          !data.legal && !data.actions.length && !data.patrones.length && !hasEnv;
        mechHidden.value = empty ? "" : JSON.stringify(data);
      });
    }
  }

  /* ------------------ Panel de firmas (lista de certificados) ------------------ */
  var firmasToggle = document.querySelector("[data-firmas-toggle]");
  var firmasPanel = document.querySelector("[data-firmas-panel]");
  var firmasClose = document.querySelector("[data-firmas-close]");
  if (firmasToggle && firmasPanel) {
    var setFirmas = function (open) {
      firmasPanel.hidden = !open;
      firmasToggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) firmasPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
    };
    firmasToggle.addEventListener("click", function () {
      setFirmas(firmasPanel.hidden);
    });
    if (firmasClose) {
      firmasClose.addEventListener("click", function () {
        setFirmas(false);
      });
    }
  }

  /* ------------------ Selector de firma ------------------ */
  var signatureSelect = document.querySelector("[data-signature-select]");
  if (signatureSelect) {
    var certifierInput = document.getElementById(
      signatureSelect.getAttribute("data-certifier") || ""
    );
    var roleInput = document.getElementById(
      signatureSelect.getAttribute("data-role") || ""
    );
    var previewWrap = signatureSelect.parentNode.querySelector("[data-firma-preview]");
    var previewImg = previewWrap
      ? previewWrap.querySelector("[data-firma-preview-img]")
      : null;

    var applySignature = function () {
      var option = signatureSelect.options[signatureSelect.selectedIndex];
      if (!option || !option.value) return;
      var name = option.getAttribute("data-name") || "";
      var role = option.getAttribute("data-role-text") || "";
      var image = option.getAttribute("data-image") || "";
      if (certifierInput && name) certifierInput.value = name;
      if (roleInput) roleInput.value = role;
      if (previewWrap && previewImg) {
        if (image) {
          previewImg.src = image;
          previewWrap.hidden = false;
        } else {
          previewImg.removeAttribute("src");
          previewWrap.hidden = true;
        }
      }
    };

    signatureSelect.addEventListener("change", applySignature);
    applySignature();
  }
})();