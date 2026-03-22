// node_modules/.pnpm/@lukeed+uuid@2.0.1/node_modules/@lukeed/uuid/dist/index.mjs
var IDX = 256;
var HEX = [];
var BUFFER;
while (IDX--) HEX[IDX] = (IDX + 256).toString(16).substring(1);
function v4() {
  var i = 0, num, out = "";
  if (!BUFFER || IDX + 16 > 256) {
    BUFFER = Array(i = 256);
    while (i--) BUFFER[i] = 256 * Math.random() | 0;
    i = IDX = 0;
  }
  for (; i < 16; i++) {
    num = BUFFER[IDX + i];
    if (i == 6) out += HEX[num & 15 | 64];
    else if (i == 8) out += HEX[num & 63 | 128];
    else out += HEX[num];
    if (i & 1 && i > 1 && i < 11) out += "-";
  }
  IDX++;
  return out;
}

// node_modules/.pnpm/solid-js@1.9.10/node_modules/solid-js/dist/solid.js
var sharedConfig = {
  context: void 0,
  registry: void 0,
  effects: void 0,
  done: false,
  getContextId() {
    return getContextId(this.context.count);
  },
  getNextContextId() {
    return getContextId(this.context.count++);
  }
};
function getContextId(count) {
  const num = String(count), len = num.length - 1;
  return sharedConfig.context.id + (len ? String.fromCharCode(96 + len) : "") + num;
}
function setHydrateContext(context) {
  sharedConfig.context = context;
}
var IS_DEV = false;
var equalFn = (a, b) => a === b;
var $PROXY = Symbol("solid-proxy");
var $TRACK = Symbol("solid-track");
var $DEVCOMP = Symbol("solid-dev-component");
var signalOptions = {
  equals: equalFn
};
var ERROR = null;
var runEffects = runQueue;
var STALE = 1;
var PENDING = 2;
var UNOWNED = {
  owned: null,
  cleanups: null,
  context: null,
  owner: null
};
var Owner = null;
var Transition = null;
var Scheduler = null;
var ExternalSourceConfig = null;
var Listener = null;
var Updates = null;
var Effects = null;
var ExecCount = 0;
function createRoot(fn, detachedOwner) {
  const listener = Listener, owner = Owner, unowned = fn.length === 0, current = detachedOwner === void 0 ? owner : detachedOwner, root = unowned ? UNOWNED : {
    owned: null,
    cleanups: null,
    context: current ? current.context : null,
    owner: current
  }, updateFn = unowned ? fn : () => fn(() => untrack(() => cleanNode(root)));
  Owner = root;
  Listener = null;
  try {
    return runUpdates(updateFn, true);
  } finally {
    Listener = listener;
    Owner = owner;
  }
}
function createSignal(value, options) {
  options = options ? Object.assign({}, signalOptions, options) : signalOptions;
  const s = {
    value,
    observers: null,
    observerSlots: null,
    comparator: options.equals || void 0
  };
  const setter = (value2) => {
    if (typeof value2 === "function") {
      if (Transition && Transition.running && Transition.sources.has(s)) value2 = value2(s.tValue);
      else value2 = value2(s.value);
    }
    return writeSignal(s, value2);
  };
  return [readSignal.bind(s), setter];
}
function createEffect(fn, value, options) {
  runEffects = runUserEffects;
  const c = createComputation(fn, value, false, STALE), s = SuspenseContext && useContext(SuspenseContext);
  if (s) c.suspense = s;
  if (!options || !options.render) c.user = true;
  Effects ? Effects.push(c) : updateComputation(c);
}
function untrack(fn) {
  if (!ExternalSourceConfig && Listener === null) return fn();
  const listener = Listener;
  Listener = null;
  try {
    if (ExternalSourceConfig) return ExternalSourceConfig.untrack(fn);
    return fn();
  } finally {
    Listener = listener;
  }
}
function on(deps, fn, options) {
  const isArray = Array.isArray(deps);
  let prevInput;
  let defer = options && options.defer;
  return (prevValue) => {
    let input;
    if (isArray) {
      input = Array(deps.length);
      for (let i = 0; i < deps.length; i++) input[i] = deps[i]();
    } else input = deps();
    if (defer) {
      defer = false;
      return prevValue;
    }
    const result = untrack(() => fn(input, prevInput, prevValue));
    prevInput = input;
    return result;
  };
}
function onCleanup(fn) {
  if (Owner === null) ;
  else if (Owner.cleanups === null) Owner.cleanups = [fn];
  else Owner.cleanups.push(fn);
  return fn;
}
function startTransition(fn) {
  if (Transition && Transition.running) {
    fn();
    return Transition.done;
  }
  const l = Listener;
  const o = Owner;
  return Promise.resolve().then(() => {
    Listener = l;
    Owner = o;
    let t;
    if (Scheduler || SuspenseContext) {
      t = Transition || (Transition = {
        sources: /* @__PURE__ */ new Set(),
        effects: [],
        promises: /* @__PURE__ */ new Set(),
        disposed: /* @__PURE__ */ new Set(),
        queue: /* @__PURE__ */ new Set(),
        running: true
      });
      t.done || (t.done = new Promise((res) => t.resolve = res));
      t.running = true;
    }
    runUpdates(fn, false);
    Listener = Owner = null;
    return t ? t.done : void 0;
  });
}
var [transPending, setTransPending] = /* @__PURE__ */ createSignal(false);
function useContext(context) {
  let value;
  return Owner && Owner.context && (value = Owner.context[context.id]) !== void 0 ? value : context.defaultValue;
}
var SuspenseContext;
function readSignal() {
  const runningTransition = Transition && Transition.running;
  if (this.sources && (runningTransition ? this.tState : this.state)) {
    if ((runningTransition ? this.tState : this.state) === STALE) updateComputation(this);
    else {
      const updates = Updates;
      Updates = null;
      runUpdates(() => lookUpstream(this), false);
      Updates = updates;
    }
  }
  if (Listener) {
    const sSlot = this.observers ? this.observers.length : 0;
    if (!Listener.sources) {
      Listener.sources = [this];
      Listener.sourceSlots = [sSlot];
    } else {
      Listener.sources.push(this);
      Listener.sourceSlots.push(sSlot);
    }
    if (!this.observers) {
      this.observers = [Listener];
      this.observerSlots = [Listener.sources.length - 1];
    } else {
      this.observers.push(Listener);
      this.observerSlots.push(Listener.sources.length - 1);
    }
  }
  if (runningTransition && Transition.sources.has(this)) return this.tValue;
  return this.value;
}
function writeSignal(node, value, isComp) {
  let current = Transition && Transition.running && Transition.sources.has(node) ? node.tValue : node.value;
  if (!node.comparator || !node.comparator(current, value)) {
    if (Transition) {
      const TransitionRunning = Transition.running;
      if (TransitionRunning || !isComp && Transition.sources.has(node)) {
        Transition.sources.add(node);
        node.tValue = value;
      }
      if (!TransitionRunning) node.value = value;
    } else node.value = value;
    if (node.observers && node.observers.length) {
      runUpdates(() => {
        for (let i = 0; i < node.observers.length; i += 1) {
          const o = node.observers[i];
          const TransitionRunning = Transition && Transition.running;
          if (TransitionRunning && Transition.disposed.has(o)) continue;
          if (TransitionRunning ? !o.tState : !o.state) {
            if (o.pure) Updates.push(o);
            else Effects.push(o);
            if (o.observers) markDownstream(o);
          }
          if (!TransitionRunning) o.state = STALE;
          else o.tState = STALE;
        }
        if (Updates.length > 1e6) {
          Updates = [];
          if (IS_DEV) ;
          throw new Error();
        }
      }, false);
    }
  }
  return value;
}
function updateComputation(node) {
  if (!node.fn) return;
  cleanNode(node);
  const time = ExecCount;
  runComputation(node, Transition && Transition.running && Transition.sources.has(node) ? node.tValue : node.value, time);
  if (Transition && !Transition.running && Transition.sources.has(node)) {
    queueMicrotask(() => {
      runUpdates(() => {
        Transition && (Transition.running = true);
        Listener = Owner = node;
        runComputation(node, node.tValue, time);
        Listener = Owner = null;
      }, false);
    });
  }
}
function runComputation(node, value, time) {
  let nextValue;
  const owner = Owner, listener = Listener;
  Listener = Owner = node;
  try {
    nextValue = node.fn(value);
  } catch (err) {
    if (node.pure) {
      if (Transition && Transition.running) {
        node.tState = STALE;
        node.tOwned && node.tOwned.forEach(cleanNode);
        node.tOwned = void 0;
      } else {
        node.state = STALE;
        node.owned && node.owned.forEach(cleanNode);
        node.owned = null;
      }
    }
    node.updatedAt = time + 1;
    return handleError(err);
  } finally {
    Listener = listener;
    Owner = owner;
  }
  if (!node.updatedAt || node.updatedAt <= time) {
    if (node.updatedAt != null && "observers" in node) {
      writeSignal(node, nextValue, true);
    } else if (Transition && Transition.running && node.pure) {
      Transition.sources.add(node);
      node.tValue = nextValue;
    } else node.value = nextValue;
    node.updatedAt = time;
  }
}
function createComputation(fn, init, pure, state = STALE, options) {
  const c = {
    fn,
    state,
    updatedAt: null,
    owned: null,
    sources: null,
    sourceSlots: null,
    cleanups: null,
    value: init,
    owner: Owner,
    context: Owner ? Owner.context : null,
    pure
  };
  if (Transition && Transition.running) {
    c.state = 0;
    c.tState = state;
  }
  if (Owner === null) ;
  else if (Owner !== UNOWNED) {
    if (Transition && Transition.running && Owner.pure) {
      if (!Owner.tOwned) Owner.tOwned = [c];
      else Owner.tOwned.push(c);
    } else {
      if (!Owner.owned) Owner.owned = [c];
      else Owner.owned.push(c);
    }
  }
  if (ExternalSourceConfig && c.fn) {
    const [track, trigger] = createSignal(void 0, {
      equals: false
    });
    const ordinary = ExternalSourceConfig.factory(c.fn, trigger);
    onCleanup(() => ordinary.dispose());
    const triggerInTransition = () => startTransition(trigger).then(() => inTransition.dispose());
    const inTransition = ExternalSourceConfig.factory(c.fn, triggerInTransition);
    c.fn = (x) => {
      track();
      return Transition && Transition.running ? inTransition.track(x) : ordinary.track(x);
    };
  }
  return c;
}
function runTop(node) {
  const runningTransition = Transition && Transition.running;
  if ((runningTransition ? node.tState : node.state) === 0) return;
  if ((runningTransition ? node.tState : node.state) === PENDING) return lookUpstream(node);
  if (node.suspense && untrack(node.suspense.inFallback)) return node.suspense.effects.push(node);
  const ancestors = [node];
  while ((node = node.owner) && (!node.updatedAt || node.updatedAt < ExecCount)) {
    if (runningTransition && Transition.disposed.has(node)) return;
    if (runningTransition ? node.tState : node.state) ancestors.push(node);
  }
  for (let i = ancestors.length - 1; i >= 0; i--) {
    node = ancestors[i];
    if (runningTransition) {
      let top = node, prev = ancestors[i + 1];
      while ((top = top.owner) && top !== prev) {
        if (Transition.disposed.has(top)) return;
      }
    }
    if ((runningTransition ? node.tState : node.state) === STALE) {
      updateComputation(node);
    } else if ((runningTransition ? node.tState : node.state) === PENDING) {
      const updates = Updates;
      Updates = null;
      runUpdates(() => lookUpstream(node, ancestors[0]), false);
      Updates = updates;
    }
  }
}
function runUpdates(fn, init) {
  if (Updates) return fn();
  let wait = false;
  if (!init) Updates = [];
  if (Effects) wait = true;
  else Effects = [];
  ExecCount++;
  try {
    const res = fn();
    completeUpdates(wait);
    return res;
  } catch (err) {
    if (!wait) Effects = null;
    Updates = null;
    handleError(err);
  }
}
function completeUpdates(wait) {
  if (Updates) {
    if (Scheduler && Transition && Transition.running) scheduleQueue(Updates);
    else runQueue(Updates);
    Updates = null;
  }
  if (wait) return;
  let res;
  if (Transition) {
    if (!Transition.promises.size && !Transition.queue.size) {
      const sources = Transition.sources;
      const disposed = Transition.disposed;
      Effects.push.apply(Effects, Transition.effects);
      res = Transition.resolve;
      for (const e2 of Effects) {
        "tState" in e2 && (e2.state = e2.tState);
        delete e2.tState;
      }
      Transition = null;
      runUpdates(() => {
        for (const d of disposed) cleanNode(d);
        for (const v of sources) {
          v.value = v.tValue;
          if (v.owned) {
            for (let i = 0, len = v.owned.length; i < len; i++) cleanNode(v.owned[i]);
          }
          if (v.tOwned) v.owned = v.tOwned;
          delete v.tValue;
          delete v.tOwned;
          v.tState = 0;
        }
        setTransPending(false);
      }, false);
    } else if (Transition.running) {
      Transition.running = false;
      Transition.effects.push.apply(Transition.effects, Effects);
      Effects = null;
      setTransPending(true);
      return;
    }
  }
  const e = Effects;
  Effects = null;
  if (e.length) runUpdates(() => runEffects(e), false);
  if (res) res();
}
function runQueue(queue) {
  for (let i = 0; i < queue.length; i++) runTop(queue[i]);
}
function scheduleQueue(queue) {
  for (let i = 0; i < queue.length; i++) {
    const item = queue[i];
    const tasks = Transition.queue;
    if (!tasks.has(item)) {
      tasks.add(item);
      Scheduler(() => {
        tasks.delete(item);
        runUpdates(() => {
          Transition.running = true;
          runTop(item);
        }, false);
        Transition && (Transition.running = false);
      });
    }
  }
}
function runUserEffects(queue) {
  let i, userLength = 0;
  for (i = 0; i < queue.length; i++) {
    const e = queue[i];
    if (!e.user) runTop(e);
    else queue[userLength++] = e;
  }
  if (sharedConfig.context) {
    if (sharedConfig.count) {
      sharedConfig.effects || (sharedConfig.effects = []);
      sharedConfig.effects.push(...queue.slice(0, userLength));
      return;
    }
    setHydrateContext();
  }
  if (sharedConfig.effects && (sharedConfig.done || !sharedConfig.count)) {
    queue = [...sharedConfig.effects, ...queue];
    userLength += sharedConfig.effects.length;
    delete sharedConfig.effects;
  }
  for (i = 0; i < userLength; i++) runTop(queue[i]);
}
function lookUpstream(node, ignore) {
  const runningTransition = Transition && Transition.running;
  if (runningTransition) node.tState = 0;
  else node.state = 0;
  for (let i = 0; i < node.sources.length; i += 1) {
    const source = node.sources[i];
    if (source.sources) {
      const state = runningTransition ? source.tState : source.state;
      if (state === STALE) {
        if (source !== ignore && (!source.updatedAt || source.updatedAt < ExecCount)) runTop(source);
      } else if (state === PENDING) lookUpstream(source, ignore);
    }
  }
}
function markDownstream(node) {
  const runningTransition = Transition && Transition.running;
  for (let i = 0; i < node.observers.length; i += 1) {
    const o = node.observers[i];
    if (runningTransition ? !o.tState : !o.state) {
      if (runningTransition) o.tState = PENDING;
      else o.state = PENDING;
      if (o.pure) Updates.push(o);
      else Effects.push(o);
      o.observers && markDownstream(o);
    }
  }
}
function cleanNode(node) {
  let i;
  if (node.sources) {
    while (node.sources.length) {
      const source = node.sources.pop(), index = node.sourceSlots.pop(), obs = source.observers;
      if (obs && obs.length) {
        const n = obs.pop(), s = source.observerSlots.pop();
        if (index < obs.length) {
          n.sourceSlots[s] = index;
          obs[index] = n;
          source.observerSlots[index] = s;
        }
      }
    }
  }
  if (node.tOwned) {
    for (i = node.tOwned.length - 1; i >= 0; i--) cleanNode(node.tOwned[i]);
    delete node.tOwned;
  }
  if (Transition && Transition.running && node.pure) {
    reset(node, true);
  } else if (node.owned) {
    for (i = node.owned.length - 1; i >= 0; i--) cleanNode(node.owned[i]);
    node.owned = null;
  }
  if (node.cleanups) {
    for (i = node.cleanups.length - 1; i >= 0; i--) node.cleanups[i]();
    node.cleanups = null;
  }
  if (Transition && Transition.running) node.tState = 0;
  else node.state = 0;
}
function reset(node, top) {
  if (!top) {
    node.tState = 0;
    Transition.disposed.add(node);
  }
  if (node.owned) {
    for (let i = 0; i < node.owned.length; i++) reset(node.owned[i]);
  }
}
function castError(err) {
  if (err instanceof Error) return err;
  return new Error(typeof err === "string" ? err : "Unknown error", {
    cause: err
  });
}
function runErrors(err, fns, owner) {
  try {
    for (const f of fns) f(err);
  } catch (e) {
    handleError(e, owner && owner.owner || null);
  }
}
function handleError(err, owner = Owner) {
  const fns = ERROR && owner && owner.context && owner.context[ERROR];
  const error = castError(err);
  if (!fns) throw error;
  if (Effects) Effects.push({
    fn() {
      runErrors(error, fns, owner);
    },
    state: STALE
  });
  else runErrors(error, fns, owner);
}
var FALLBACK = Symbol("fallback");

// packages/anywidget/src/widget.js
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
function is_href(str) {
  return str.startsWith("http://") || str.startsWith("https://");
}
async function load_css_href(href, anywidget_id) {
  let prev = document.querySelector(`link[id='${anywidget_id}']`);
  if (prev) {
    let newLink = (
      /** @type {HTMLLinkElement} */
      prev.cloneNode()
    );
    newLink.href = href;
    newLink.addEventListener("load", () => prev?.remove());
    newLink.addEventListener("error", () => prev?.remove());
    prev.after(newLink);
    return;
  }
  return new Promise((resolve) => {
    let link = Object.assign(document.createElement("link"), {
      rel: "stylesheet",
      href,
      onload: resolve
    });
    document.head.appendChild(link);
  });
}
function load_css_text(css_text, anywidget_id) {
  let prev = document.querySelector(`style[id='${anywidget_id}']`);
  if (prev) {
    prev.textContent = css_text;
    return;
  }
  let style = Object.assign(document.createElement("style"), {
    id: anywidget_id,
    type: "text/css"
  });
  style.appendChild(document.createTextNode(css_text));
  document.head.appendChild(style);
}
async function load_css(css, anywidget_id) {
  if (!css || !anywidget_id) return;
  if (is_href(css)) return load_css_href(css, anywidget_id);
  return load_css_text(css, anywidget_id);
}
async function load_esm(esm) {
  if (is_href(esm)) {
    return await import(
      /* webpackIgnore: true */
      /* @vite-ignore */
      esm
    );
  }
  let url = URL.createObjectURL(new Blob([esm], { type: "text/javascript" }));
  let mod = await import(
    /* webpackIgnore: true */
    /* @vite-ignore */
    url
  );
  URL.revokeObjectURL(url);
  return mod;
}
function warn_render_deprecation(anywidget_id) {
  console.warn(`[anywidget] Deprecation Warning for ${anywidget_id}: Direct export of a 'render' will likely be deprecated in the future. To migrate ...

Remove the 'export' keyword from 'render'
-----------------------------------------

export function render({ model, el }) { ... }
^^^^^^

Create a default export that returns an object with 'render'
------------------------------------------------------------

function render({ model, el }) { ... }
         ^^^^^^
export default { render }
                 ^^^^^^

Pin to anywidget>=0.9.0 in your pyproject.toml
----------------------------------------------

dependencies = ["anywidget>=0.9.0"]

To learn more, please see: https://github.com/manzt/anywidget/pull/395.
`);
}
async function load_widget(esm, anywidget_id) {
  let mod = await load_esm(esm);
  if (mod.render) {
    warn_render_deprecation(anywidget_id);
    return {
      async initialize() {
      },
      render: mod.render
    };
  }
  assert(
    mod.default,
    `[anywidget] module must export a default function or object.`
  );
  let widget = typeof mod.default === "function" ? await mod.default() : mod.default;
  return widget;
}
var INITIALIZE_MARKER = Symbol("anywidget.initialize");
function model_proxy(model, context) {
  return {
    get: model.get.bind(model),
    set: model.set.bind(model),
    save_changes: model.save_changes.bind(model),
    send: model.send.bind(model),
    // @ts-expect-error
    on(name, callback) {
      model.on(name, callback, context);
    },
    off(name, callback) {
      model.off(name, callback, context);
    },
    // @ts-expect-error - the widget_manager type is wider than what
    // we want to expose to developers.
    // In a future version, we will expose a more limited API but
    // that can wait for a minor version bump.
    widget_manager: model.widget_manager
  };
}
async function safe_cleanup(fn, kind) {
  return Promise.resolve().then(() => fn?.()).catch((e) => console.warn(`[anywidget] error cleaning up ${kind}.`, e));
}
function throw_anywidget_error(source) {
  if (!(source instanceof Error)) {
    throw source;
  }
  let lines = source.stack?.split("\n") ?? [];
  let anywidget_index = lines.findIndex((line) => line.includes("anywidget"));
  let clean_stack = anywidget_index === -1 ? lines : lines.slice(0, anywidget_index + 1);
  source.stack = clean_stack.join("\n");
  console.error(source);
  throw source;
}
function invoke(model, name, msg, options = {}) {
  let id = v4();
  let signal = options.signal ?? AbortSignal.timeout(3e3);
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(signal.reason);
    }
    signal.addEventListener("abort", () => {
      model.off("msg:custom", handler);
      reject(signal.reason);
    });
    function handler(msg2, buffers) {
      if (!(msg2.id === id)) return;
      resolve([msg2.response, buffers]);
      model.off("msg:custom", handler);
    }
    model.on("msg:custom", handler);
    model.send(
      { id, kind: "anywidget-command", name, msg },
      void 0,
      options.buffers ?? []
    );
  });
}
function promise_with_resolvers() {
  let resolve;
  let reject;
  let promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}
function observe(model, name, { signal }) {
  let [get, set] = createSignal(model.get(name));
  let update = () => set(() => model.get(name));
  model.on(`change:${name}`, update);
  signal?.addEventListener("abort", () => {
    model.off(`change:${name}`, update);
  });
  return get;
}
var Runtime = class {
  /** @type {solid.Accessor<Result<AnyWidget>>} */
  // @ts-expect-error - Set synchronously in constructor.
  #widget_result;
  /** @type {AbortSignal} */
  #signal;
  /** @type {Promise<void>} */
  ready;
  /**
   * @param {base.DOMWidgetModel} model
   * @param {{ signal: AbortSignal }} options
   */
  constructor(model, options) {
    let resolvers = promise_with_resolvers();
    this.ready = resolvers.promise;
    this.#signal = options.signal;
    this.#signal.throwIfAborted();
    this.#signal.addEventListener("abort", () => dispose());
    AbortSignal.timeout(2e3).addEventListener("abort", () => {
      resolvers.reject(new Error("[anywidget] Failed to initialize model."));
    });
    let dispose = createRoot((dispose2) => {
      let typed_model = model;
      let id = typed_model.get("_anywidget_id");
      let css = observe(typed_model, "_css", { signal: this.#signal });
      let esm = observe(typed_model, "_esm", { signal: this.#signal });
      let [widget_result, set_widget_result] = createSignal(
        /** @type {Result<AnyWidget>} */
        { status: "pending" }
      );
      this.#widget_result = widget_result;
      createEffect(
        on(
          css,
          () => console.debug(`[anywidget] css hot updated: ${id}`),
          { defer: true }
        )
      );
      createEffect(
        on(
          esm,
          () => console.debug(`[anywidget] esm hot updated: ${id}`),
          { defer: true }
        )
      );
      createEffect(() => {
        load_css(css(), id);
      });
      createEffect(() => {
        let controller = new AbortController();
        onCleanup(() => controller.abort());
        model.off(null, null, INITIALIZE_MARKER);
        load_widget(esm(), id).then(async (widget) => {
          if (controller.signal.aborted) {
            return;
          }
          let cleanup = await widget.initialize?.({
            model: model_proxy(model, INITIALIZE_MARKER),
            experimental: {
              // @ts-expect-error - bind isn't working
              invoke: invoke.bind(null, model)
            }
          });
          if (controller.signal.aborted) {
            safe_cleanup(cleanup, "esm update");
            return;
          }
          controller.signal.addEventListener(
            "abort",
            () => safe_cleanup(cleanup, "esm update")
          );
          set_widget_result({ status: "ready", data: widget });
          resolvers.resolve();
        }).catch((error) => set_widget_result({ status: "error", error }));
      });
      return dispose2;
    });
  }
  /**
   * @param {base.DOMWidgetView} view
   * @param {{ signal: AbortSignal }} options
   * @returns {Promise<void>}
   */
  async create_view(view, options) {
    let model = view.model;
    let signal = AbortSignal.any([this.#signal, options.signal]);
    signal.throwIfAborted();
    signal.addEventListener("abort", () => dispose());
    let dispose = createRoot((dispose2) => {
      createEffect(() => {
        model.off(null, null, view);
        view.$el.empty();
        let result = this.#widget_result();
        if (result.status === "pending") {
          return;
        }
        if (result.status === "error") {
          throw_anywidget_error(result.error);
          return;
        }
        let controller = new AbortController();
        onCleanup(() => controller.abort());
        Promise.resolve().then(async () => {
          let cleanup = await result.data.render?.({
            model: model_proxy(model, view),
            el: view.el,
            experimental: {
              // @ts-expect-error - bind isn't working
              invoke: invoke.bind(null, model)
            }
          });
          if (controller.signal.aborted) {
            safe_cleanup(cleanup, "dispose view - already aborted");
            return;
          }
          controller.signal.addEventListener(
            "abort",
            () => safe_cleanup(cleanup, "dispose view - aborted")
          );
        }).catch((error) => throw_anywidget_error(error));
      });
      return () => dispose2();
    });
  }
};
var version = "0.9.21";
function widget_default({ DOMWidgetModel, DOMWidgetView }) {
  let RUNTIMES = /* @__PURE__ */ new WeakMap();
  class AnyModel extends DOMWidgetModel {
    static model_name = "AnyModel";
    static model_module = "anywidget";
    static model_module_version = version;
    static view_name = "AnyView";
    static view_module = "anywidget";
    static view_module_version = version;
    /** @param {Parameters<InstanceType<DOMWidgetModel>["initialize"]>} args */
    initialize(...args) {
      super.initialize(...args);
      let controller = new AbortController();
      this.once("destroy", () => {
        controller.abort("[anywidget] Runtime destroyed.");
        RUNTIMES.delete(this);
      });
      RUNTIMES.set(this, new Runtime(this, { signal: controller.signal }));
    }
    /** @param {Parameters<InstanceType<DOMWidgetModel>["_handle_comm_msg"]>} msg */
    async _handle_comm_msg(...msg) {
      let runtime = RUNTIMES.get(this);
      await runtime?.ready;
      return super._handle_comm_msg(...msg);
    }
    /**
     * @param {Record<string, any>} state
     *
     * We override to support binary trailets because JSON.parse(JSON.stringify())
     * does not properly clone binary data (it just returns an empty object).
     *
     * https://github.com/jupyter-widgets/ipywidgets/blob/47058a373d2c2b3acf101677b2745e14b76dd74b/packages/base/src/widget.ts#L562-L583
     */
    serialize(state) {
      let serializers = (
        /** @type {DOMWidgetModel} */
        this.constructor.serializers || {}
      );
      for (let k of Object.keys(state)) {
        try {
          let serialize = serializers[k]?.serialize;
          if (serialize) {
            state[k] = serialize(state[k], this);
          } else if (k === "layout" || k === "style") {
            state[k] = JSON.parse(JSON.stringify(state[k]));
          } else {
            state[k] = structuredClone(state[k]);
          }
          if (typeof state[k]?.toJSON === "function") {
            state[k] = state[k].toJSON();
          }
        } catch (e) {
          console.error("Error serializing widget state attribute: ", k);
          throw e;
        }
      }
      return state;
    }
  }
  class AnyView extends DOMWidgetView {
    #controller = new AbortController();
    async render() {
      let runtime = RUNTIMES.get(this.model);
      assert(runtime, "[anywidget] Runtime not found.");
      await runtime.create_view(this, { signal: this.#controller.signal });
    }
    remove() {
      this.#controller.abort("[anywidget] View destroyed.");
      super.remove();
    }
  }
  return { AnyModel, AnyView };
}

// packages/anywidget/src/index.js
define(["@jupyter-widgets/base"], widget_default);
